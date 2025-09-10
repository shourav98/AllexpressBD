from django.urls import path
from . import views

urlpatterns = [
    # Store home
    path("", views.store, name="store"),

    # Browse by category
    path("category/<slug:category_slug>/", views.store, name="products_by_category"),

    # Browse by brand
    path("brand/<slug:brand_slug>/", views.products_by_brand, name="products_by_brand"),

    # Product detail (category-based)
    path("category/<slug:category_slug>/<slug:product_slug>/", views.product_detail, name="product_detail"),

    # Product detail (brand-based)
    path("brand/<slug:brand_slug>/<slug:product_slug>/", views.product_detail, name="product_detail_by_brand"),

    # Search
    path("search/", views.search, name="search"),

    # Submit review
    path("submit_review/<int:product_id>/", views.submit_review, name="submit_review"),

    
    
    path("brand/<slug:brand_slug>/", views.store, name="products_by_brand"),


    path("product/create/", views.product_create, name="product_create"),
    path("product/<int:product_id>/add-variation/", views.add_variation_ajax, name="add_variation_ajax"),

]


# urlpatterns = [
#     path("",views.store, name= "store"),
#     path('category/<slug:category_slug>/',views.store, name= "products_by_category"),
#     path('category<slug:category_slug>/<slug:product_slug>/',views.product_detail, name= "product_detail"),
#     path('search/',views.search, name = 'search'),
#     path("submit_review/<int:product_id>/",views.submit_review, name="submit_review"),
    
    
#     path('category/<slug:category_slug>/product/<slug:product_slug>/', views.product_detail, name='product_detail'),
    
#     path('category/<slug:category_slug>/', views.store, name='store_by_category'),
#     path('', views.store, name='store'),  # Default store view without category



#     path('<slug:category_slug>/<slug:product_slug>/', views.product_detail, name="product_detail"),
#     path('brand/<slug:brand_slug>/', views.products_by_brand, name="products_by_brand"),


# ]