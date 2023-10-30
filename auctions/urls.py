from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("create/", views.create_listing, name="create"),
    path("categories/", views.categories, name="categories"),
    path("category/<int:category_id>/", views.category_active, name="category_active"),
    path("watchlist/", views.watchlist, name="watchlist"),
    path("watchlist/<int:listing_id>/", views.watchlist, name="watchlist_listing"),
    path("bid/<int:listing_id>/", views.place_bid, name="place_bid"),
    path("comment/<int:listing_id>/", views.add_comment, name="add_comment"),
    path("close/<int:listing_id>/", views.close_auction, name="close_auction"),
    path("listing/<int:listing_id>/", views.listing_page, name="listing_page")
]
