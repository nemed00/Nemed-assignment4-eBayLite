from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Max
from .models import Listing, Category, Bid, Comment, Watchlist
from .forms import ListingForm, BidForm
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from .models import User


def index(request):
    active_listings = Listing.objects.filter(active=True)
    # Annotate the active listings with the current highest bid
    active_listings = active_listings.annotate(max_bid_ammount=Max('bid__amount'))

    return render(request, "auctions/index.html", {"active_listings": active_listings})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            # Accessing user.watchlist will create the Watchlist if it doesn't exist
            #user.watchlist

            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.creator = request.user
            listing.current_bid = listing.starting_bid
            listing.save()
            return redirect("index")
    else:
        form = ListingForm()
        form.fields['category'].queryset = Category.objects.all()

    
    return render(request, "auctions/create.html", {"form": form})

def categories(request):
    categories = Category.objects.all()
    return render(request, "auctions/categories.html", {"categories": categories})

def category_active(request, category_id):
    try:
        category = Category.objects.get(pk=category_id)
        active_listings = Listing.objects.filter(category=category, active=True)
    except Category.DoesNotExist:
        # Handle the case where the category does not exist
        return render(request, "error.html", {"error_message": "Category not found"})
    
    return render(request, "auctions/category_active.html", {"category": category, "active_listings": active_listings})

@login_required
def watchlist(request):
    user = request.user

    if request.method == "POST":
        listing_id = request.POST.get('listing_id')
        action = request.POST.get('action')

        # Get the user's watchlist
        watchlist, created = Watchlist.objects.get_or_create(user=user)

        listing = Listing.objects.get(pk=listing_id)

        if action == "add_to_watchlist":
            watchlist.listings.add(listing)
        elif action == "remove_from_watchlist":
            watchlist.listings.remove(listing)

    # Get the user's updated watchlist
    watchlist_items = user.user_watchlist.all()
    return render(request, "auctions/watchlist.html", {"watchlist_items": watchlist_items})



def place_bid(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    if request.method == "POST":
        form = BidForm(request.POST)
        if form.is_valid():
            bid_amount = form.cleaned_data['bid_amount']
            user = request.user

            if bid_amount >= listing.starting_bid and bid_amount > listing.current_bid:
                Bid.objects.create(user=user, listing=listing, amount=bid_amount)
                listing.current_bid = bid_amount
                listing.save()
                return HttpResponseRedirect(reverse('listing_page', args=(listing_id,)))
            else:
                form.add_error('bid_amount', 'Invalid bid amount. It must be greater than the current bid and at least as large as the starting bid.')

    else:
        form = BidForm()

    return render(request, "auctions/listing_page.html", {"listing": listing, "form": form})

def close_auction(request, listing_id):
    user = request.user
    listing = get_object_or_404(Listing, pk=listing_id)

    # Check if the user is the creator of the listing
    if user == listing.creator:
        # Check if the listing is already closed
        if not listing.active:
            return HttpResponseRedirect(reverse('listing_page', args=(listing_id,)))

        # Determine the highest bidder
        highest_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()

        if highest_bid:
            # Set the highest bidder as the winner
            listing.winner = highest_bid.user
        else:
            # If no bids were placed, the creator is the winner
            listing.winner = user

        # Mark the listing as inactive
        listing.active = False
        listing.save()

    return HttpResponseRedirect(reverse('listing_page', args=(listing_id,)))

def add_comment(request, listing_id):
    user = request.user
    listing = get_object_or_404(Listing, pk=listing_id)

    if request.method == "POST":
        comment_text = request.POST["comment_text"]
        Comment.objects.create(user=user, listing=listing, text=comment_text)

    return HttpResponseRedirect(reverse('listing_page', args=(listing_id,)))


def listing_page(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    user = request.user

    # Check if the user is signed in
    if request.method == "POST" and user.is_authenticated:
        # Check for form submissions (e.g., Watchlist, Bid, Close Auction, Comment)

        # Implement Watchlist feature
        if "Add to Watchlist" in request.POST:
            # Add the listing to the user's watchlist
            user.user_watchlist.add(listing)
            #watchlist(request)
        elif "Remove from Watchlist" in request.POST:
            # Remove the listing from the user's watchlist
            user.watchlist.remove(listing)

        # Implement Bid feature
        if "place_bid" in request.POST:
            # Handle bid form submission
            form = BidForm(request.POST)
            if form.is_valid():
                bid_amount = form.cleaned_data['bid_amount']
                #user = request.user
                # Check if the bid is valid
                if bid_amount >= listing.starting_bid and (not listing.winner) and (not user == listing.creator) and (bid_amount > listing.current_bid):
                    # Create a Bid object to record the bid
                    Bid.objects.create(user=user, listing=listing, amount=bid_amount)
                    listing.current_bid = bid_amount
                    listing.save()
                else:
                    # Handle invalid bid, you can add an error message to the form
                    form.add_error('bid_amount', 'Invalid bid amount. It must be greater than the current bid and at least as large as the starting bid.')
                    # Ensure the bid is valid and greater than the current highest bid

        # Implement Close Auction feature
        if "close_auction" in request.POST:
            # Check if the user is the creator of the listing
            if listing.creator == user:
                # Close the auction and determine the winner
                if listing.active:
                    highest_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()
                    if highest_bid:
                        listing.winner = highest_bid.user
                    else:
                        # If no bids were placed, the creator is the winner
                        listing.winner = user

                    listing.active = False
                    listing.save()

        # Implement Comment feature
        if "add_comment" in request.POST:
            # Handle comment form submission
            text = request.POST["comment_text"]
            comment = Comment(listing=listing, user=user, text=text)
            comment.save()
            # You can also add validation and error handling here


    # Fetch comments related to the listing
    comments = Comment.objects.filter(listing=listing)
    max_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()
    current_bid = max_bid.amount if max_bid else listing.starting_bid


    return render(request, "auctions/listing_page.html", {
        "listing": listing,
        "user": user,
        "comments": comments,
        "current_bid": current_bid
    })

