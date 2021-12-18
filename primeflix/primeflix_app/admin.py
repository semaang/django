from django.contrib import admin
from primeflix_app.models import Category, Theme, Product, Review, Customer, Order, OrderLine, ShippingAddress
########
from django.urls import path
from django.shortcuts import render
from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse

class CsvImportForm(forms.Form):
    csv_upload = forms.FileField()

class ProductAdmin(admin.ModelAdmin):
    # list_display = ('title', 'price')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]
            
            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)
            
            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
            
                created = Product.objects.update_or_create(
                    category = Category.objects.get(pk=int(fields[0])),
                    theme = Theme.objects.get(id=int(fields[1])),
                    title = fields[2],
                    description = fields[3],
                    price = float(fields[4]),
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)
        print("Ok")
        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)

admin.site.register(Product, ProductAdmin)




# Register your models here.

admin.site.register(Category)
admin.site.register(Theme)
# admin.site.register(Product)
admin.site.register(Review)
admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(OrderLine)
admin.site.register(ShippingAddress)


