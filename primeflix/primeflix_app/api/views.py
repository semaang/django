# from re import search
from django.conf import settings
from django.db.models.query import QuerySet
from django.http import JsonResponse
from django.http.response import HttpResponse
from rest_framework.response import Response
from rest_framework import generics, serializers, status
from rest_framework.decorators import api_view
from rest_framework.views import APIView, View
from rest_framework import mixins
from rest_framework import generics
from rest_framework.exceptions import APIException, ValidationError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from stripe.api_resources import checkout
from primeflix_app.models import User, Category, Theme, Product, Review, Customer, Order, OrderLine, ShippingAddress
from primeflix_app.api.serializers import CategorySerializer, ThemeSerializer, ProductSerializer, ReviewSerializer, CustomerSerializer, OrderSerializer, OrderLineSerializer, ShippingAddressSerializer
from primeflix_app.api.permissions import IsAdminOrReadyOnly, IsReviewUserOrReadOnly, IsOrderUser
from django.urls import reverse
from django.dispatch import receiver

import stripe


# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


def refresh_ratings():
        products = Product.objects.all()
        if (products.exists()):
            for p in products:
                reviews = Review.objects.filter(product=p)
                if (reviews.exists()):
                    p.number_ratings=reviews.count()
                    average_rating = 0
                    for r in reviews:
                        average_rating = average_rating + r.rating
                    average_rating = average_rating/reviews.count()
                    p.average_rating = average_rating 
                    p.save()
                        
def set_order_init():  
    customers = Customer.objects.all()
    
    if customers.exists():
        for c in customers:
            orders = Order.objects.filter(customer=c, order_paid=False)
            if orders.exists():
                pass
            else:
                print(type(c.id))
                order = Order()
                order.customer = c
                order.save()
                
                
     

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSessionView(APIView):
    def post(self, request, *args, **kwargs):
        # YOUR_DOMAIN = "http://127.0.0.1:8000"
        checkout_session = stripe.checkout.Session.create(
            payment_method_types = ['card'],
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': '{{PRICE_ID}}',
                    'quantity': 1,
                },
            ],
            mode='payment',
            # success_url=YOUR_DOMAIN + '/success/',
            # cancel_url=YOUR_DOMAIN + '/cancel/',
        )
        
        return JsonResponse({'id' : checkout_session.id})


# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


class ReviewList(generics.ListAPIView):
    # queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    # permission_classes = [IsAuthenticated]
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        pk = self.kwargs['pk']
        return Review.objects.filter(product=pk)
        

class ReviewCreate(generics.CreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Review.objects.all()
    
    def perform_create(self, serializer):
        pk = self.kwargs['pk']
        temp_product = Product.objects.get(pk=pk)
    
        temp_review_user = self.request.user
        review_queryset = Review.objects.filter(product=temp_product, review_user=temp_review_user)
        
        if (review_queryset.exists()):
            raise ValidationError("you have already reviewed this product")
        
        if (temp_product.number_ratings == 0):
            temp_product.average_rating = serializer.validated_data['rating']
        else:
            temp_product.average_rating = ((temp_product.average_rating * temp_product.number_ratings ) + float(serializer.validated_data['rating'])) / float(temp_product.number_ratings + 1) 

        temp_product.number_ratings = temp_product.number_ratings + 1
        temp_product.save()  
        serializer.save(product=temp_product, review_user=temp_review_user)
            
    
class ReviewDetails(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    # permission_classes = [IsAuthenticatedOrReadOnly] /////////////////////////////////////////////:
    permission_classes = [IsReviewUserOrReadOnly]
    
    def delete(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        temp_review = Review.objects.get(pk=pk)
        temp_product = Product.objects.get(pk=temp_review.product.id)
        
        if(temp_product.number_ratings > 1):      
            temp_product.average_rating = ((temp_product.average_rating * temp_product.number_ratings ) - temp_review.rating) / (temp_product.number_ratings - 1)
        else:
             temp_product.average_rating = 0
             
        temp_product.number_ratings = temp_product.number_ratings - 1 
        temp_product.save()
        return self.destroy(request, *args, **kwargs)
    
    
    def perform_update(self, serializer):
        # temp_review = Review.objects.get(pk=pk)
        pk = self.kwargs['pk']
        temp_review = Review.objects.get(pk=pk)
        temp_product = Product.objects.get(pk=temp_review.product.id)
        
        if(temp_product.number_ratings > 0):      
            temp_product.average_rating = ((temp_product.average_rating * temp_product.number_ratings ) - temp_review.rating + serializer.validated_data['rating']) / temp_product.number_ratings
        else:
            temp_product.average_rating = temp_review.rating
             
        temp_product.save()  
        serializer.save(product=temp_product)


# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    
    
class OrderListPaid(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer    
    
    def get_queryset(self):
        pk = self.kwargs['pk']
        return Order.objects.filter(order_user=pk, order_paid=True)
    
    
class OrderLines(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderLineSerializer
    
    def get_queryset(self):
        pk = self.kwargs['pk']
        
        temp_order = Order.objects.get(order_user=pk, order_paid=False)
        
        if (self.request.user != temp_order.order_user):
            raise ValidationError("denied")
        
        if temp_order:
            return OrderLine.objects.filter(orderLine_user=pk, order=temp_order) 
        else:
            return ('Error : OrderLine doesn t exist in database')
            
    def perform_create(self, serializer):
            pk = self.kwargs['pk']
            temp_order = Order.objects.get(order_user=pk, order_paid=False)
        
            if (self.request.user != temp_order.order_user):
                raise ValidationError("denied")
            
            # temp_customer = Customer.objects.get(pk=pk)
            temp_order = Order.objects.get(pk=pk, order_paid=False)
            serializer.save(order=temp_order, orderLine_user=temp_order.order_user)
              
 
class OrderLineDetails(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderLineSerializer
    
    def get_queryset(self):    
        pk = self.kwargs["pk"]
        ol = OrderLine.objects.get(pk=pk)
        if (self.request.user != ol.orderLine_user):
            raise ValidationError("denied")
        return OrderLine.objects.all()
  
  
    def delete(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        temp_orderline = OrderLine.objects.get(pk=pk)

        if (self.request.user != temp_orderline.order.order_user):
            raise ValidationError("denied")
        
        temp_order = Order.objects.filter(order_user=temp_orderline.order.order_user, order_paid=False)
        if temp_order.exists():
            return self.destroy(request, *args, **kwargs)
        else:
            raise ValidationError("denied")
    
    
    def perform_update(self, serializer):
        pk = self.kwargs['pk']
        # serializer.save()
        
        temp_orderline = OrderLine.objects.get(pk=pk)

        if (self.request.user != temp_orderline.order.order_user):
            raise ValidationError("denied")
                
        # temp_order = Order.objects.filter(pk=temp_orderline.order.id, order_paid=False)
        temp_order = Order.objects.get(pk=temp_orderline.order.id)
        
        if ((temp_orderline.order == temp_order) and (temp_orderline.order.order_paid == False)):
            serializer.save()

        else:
            raise APIException("Order paid")

    
class OrderDetails(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        pk = self.kwargs['pk']
        
        order_query = Order.objects.get(order_user=pk)        
        if (self.request.user != order_query.order_user):
            raise ValidationError("you can't access this page")
        
        try:
            temp_order = Order.objects.get(order_user=pk, order_paid=False)
        except Order.DoesNotExist:
            return Response('Error : Order doesn\'t exist in database', status=status.HTTP_404_NOT_FOUND)
        
        serializer = OrderSerializer(temp_order)
        
        print(*serializer.data)
        
        print(type(self.kwargs))
        print(self.kwargs)
        print(temp_order.date_ordered)
        for key, value in serializer.data.items():
            print("'''''''''''''''''''''''''''''''''''''''''''''")
            print(key)
            print("'''''''''''''''''''''''''''''''''''''''''''''")
            print(value)
        
        
        return Response(serializer.data) 


# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    
    
class CategoryList(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadyOnly]
    
    def get_queryset(self):
        # pk = self.kwargs['pk']
        # return Review.objects.filter(product=pk)
        return Category.objects.all()
    
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if(serializer.is_valid()):
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class CategoryDetails(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadyOnly]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    
    
class ThemeList(generics.ListAPIView):
    serializer_class = ThemeSerializer
    # permission_classes = [IsAuthenticatedOrReadOnly]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Theme.objects.all()
    
    def post(self, request):
        serializer = ThemeSerializer(data=request.data)
        if(serializer.is_valid()):
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class ThemeDetails(generics.RetrieveUpdateDestroyAPIView):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer


# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            
class CustomerList(APIView):
    # permission_classes = [IsAuthenticated]
    permission_classes = [IsAdminOrReadyOnly]

    def get(self, request):
        customers = Customer.objects.all()
        serializer = CustomerSerializer(customers, many=True)
        
        orderline = OrderLineDetails.objects.get(id=1)
        print("HOLAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        print(orderline.quantity)
        print("")
        print("HOLAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        return Response(serializer.data)
 
# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                
class ProductList(APIView):
    permission_classes = [IsAdminOrReadyOnly]

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        
        refresh_ratings()
        set_order_init()
        
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if(serializer.is_valid()):
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

   


class ProductDetails(APIView):
    permission_classes = [IsAdminOrReadyOnly]
    
    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response('Error : Film doesn\'t exist in database', status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProductSerializer(product)
        return Response(serializer.data) 
    
    def put(self, request, pk):
        product = Product.objects.get(pk=pk)
        serializer = ProductSerializer(product, data=request.data)
        if(serializer.is_valid()):
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors) 
    
    def delete(self, request, pk):       
            product = Product.objects.get(pk=pk)
            product.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)        
 
 
 
 
 # /////////////////////////////////////////////////////////////////////////////////////////////////////        

 
 
 
# class StreamPlatformDetailsAV(APIView):
#     permission_classes = [IsAdminOrReadyOnly]

#     def get(self, request, pk):
#         try:
#             platform = StreamPlatformList.objects.get(pk=pk)
#         except StreamPlatformList.DoesNotExist:
#             return Response('Error : Platform doesn\'t exist in database', status=status.HTTP_404_NOT_FOUND)
        
#         serializer = StreamPlatformListSerializer(platform)
#         return Response(serializer.data) 
      
#     def put(self, request, pk):
#         platform = StreamPlatformList.objects.get(pk=pk)
#         serializer = StreamPlatformListSerializer(platform, data=request.data)
#         if(serializer.is_valid()):
#             serializer.save()
#             return Response(serializer.data)
#         else:
#             return Response(serializer.errors) 
    
#     def delete(self, request, pk):       
#             platform = StreamPlatformList.objects.get(pk=pk)
#             platform.delete()
#             return Response(status=status.HTTP_204_NO_CONTENT)     
 
 
 
# /////////////////////////////////////////////////////////////////////////////////////////////////////        




# # many=True :> MovieSerializer needs to consult multiple (not only a single)
# # objects in the query set and map them
# @api_view(['GET', 'POST'])
# def movie_list(request):
    
#     if (request.method == 'GET'): 
#         movies = Movie.objects.all()
#         serializer = MovieSerializer(movies, many=True)
#         return Response(serializer.data) 
      
#     if (request.method == 'POST'): 
#         serializer = MovieSerializer(data=request.data)
#         if(serializer.is_valid()):
#             serializer.save()
#             return Response(serializer.data)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['GET', 'PUT', 'DELETE'])
# def movie_details(request, pk):
    
#     if(request.method == 'GET'): 
#         try:
#             movie = Movie.objects.get(pk=pk)
#         except Movie.DoesNotExist:
#             return Response('Error : Film inexistant', status=status.HTTP_404_NOT_FOUND)
        
#         serializer = MovieSerializer(movie)
#         return Response(serializer.data)   
     
#     if(request.method == 'PUT'):
#         movie = Movie.objects.get(pk=pk)
#         serializer = MovieSerializer(movie, data=request.data)
#         if(serializer.is_valid()):
#             serializer.save()
#             return Response(serializer.data)
#         else:
#             return Response(serializer.errors) 
           
#     if(request.method == 'DELETE'):   
#         movie = Movie.objects.get(pk=pk)
#         movie.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)



def index(request):
    message = "Hello World"
    return HttpResponse(message)

def add_numbers():
    l = [1,2,3]
    return l

def add_test():
    d = {'voiture' : 'golff', 'fille' : 'claudette'}
    return d
    
# def index(request):
#     message = add_numbers()
#     message.append("coucFou")
    
#     message2 = add_test()
#     print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
#     print(message2)
#     print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
#     print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
#     # print(**message2)
#     print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
#     print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

#     for i in message:
#         print(i)
#     print (message)
#     print (*message)
#     print(type(message))
#     print(type(message2))
    
#     for key, value in message2.items():
#         print("'''''''''''''''''''''''''''''''''''''''''''''")
#         print(key)
#         print("'''''''''''''''''''''''''''''''''''''''''''''")
#         print(value)

#     # print(type(*message))
    
#     orderL_temp = OrderLine.objects.get(pk=7)
#     print(orderL_temp)
#     test = orderL_temp.get_total_orderLine()
   
    
#     print(test)
    
#     order_temp = Order.objects.get(pk=5)
#     print(order_temp.get_total_order())
#     test = order_temp.get_total_order()
      
#     print(test)
   
   
   
#     print("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
#     # print(orderL_temp.get_total_OL())
#     return HttpResponse(test)



# def Products (request):
#     # if (request.method == 'GET'): 
#         queryset_products = Product.objects.all()
#         serializer = ProductSerializer(queryset_products, many=True)
#         print("11111111111111111111111111111111111111111111111111111111111")
#         print(type(queryset_products))
#         print("222222222222222222222222222222222222222222222222")

#         print(queryset_products)
#         print("33333333333333333333333333333333333333")
#         print(type(serializer))
#         print("44444444444444444444444444")

#         print(dir(serializer))
#         print("5555555555555555555555555555555555555555")
#         print(type(serializer.data))
#         print("666666666666666666666666666666666666666666666666")
#         print(vars(serializer))
#         print("7777777777777777777777777777777777777777777777777777777777")
#         print("")
        
#         return Response(serializer.data)
    
#     if (request.method == 'GET'): 
#         movies = Movie.objects.all()
#         serializer = MovieSerializer(movies, many=True)
#         return Response(serializer.data) 

# @api_view(['GET', 'POST'])
# def Categories (request):
#     if (request.method == 'GET'): 

#         queryset_products = Category.objects.all()
#         serializer = CategorySerializer(queryset_products, many=True)    
#         return Response(serializer.data) 

#     if (request.method == 'POST'): 
#         serializer = CategorySerializer(data=request.data)
#         if(serializer.is_valid()):
#             serializer.save()
#             return Response(serializer.data)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['GET', 'PUT', 'DELETE'])
# def CategoryDetailsTEST(request, pk):
    
#     if(request.method == 'GET'): 
#         try:
#             category = Category.objects.get(pk=pk)
#         except Category.DoesNotExist:
#             return Response('Error : Category inexistant', status=status.HTTP_404_NOT_FOUND)
        
#         serializer = CategorySerializer(category)
#         # print(type(name))
#         return Response({serializer.data})   
