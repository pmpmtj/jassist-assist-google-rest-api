from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Contact
from .forms import ContactForm
import logging

logger = logging.getLogger(__name__)

@login_required
def contact_list(request):
    """
    View for listing user's contacts with pagination.
    """
    # Get optional category filter
    category = request.GET.get('category', '')
    
    # Filter contacts by user and optionally by category
    if category:
        contacts = Contact.objects.filter(user=request.user, category=category).order_by('name')
    else:
        contacts = Contact.objects.filter(user=request.user).order_by('name')
    
    # Get all unique categories for this user for the filter dropdown
    categories = Contact.objects.filter(user=request.user).values_list('category', flat=True).distinct()
    categories = [c for c in categories if c]  # Remove empty categories
    
    # Paginate the results - 10 contacts per page
    paginator = Paginator(contacts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    logger.debug(f"Listing contacts for user: {request.user.username}, page: {page_number}, filter: {category}")
    return render(request, 'contacts/list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category,
        'title': 'My Contacts'
    })

@login_required
def contact_detail(request, contact_id):
    """
    View for displaying detailed information about a specific contact.
    """
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    
    logger.debug(f"Viewing contact details for: {contact.name}")
    return render(request, 'contacts/detail.html', {
        'contact': contact,
        'title': contact.name
    })

@login_required
def contact_create(request):
    """
    View for creating a new contact.
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.user = request.user
            contact.save()
            
            logger.info(f"User {request.user.username} created a new contact: {contact.name}")
            messages.success(request, f"Contact '{contact.name}' has been created successfully.")
            return redirect('contacts:detail', contact_id=contact.id)
    else:
        form = ContactForm()
    
    logger.debug(f"Rendering contact creation form for user: {request.user.username}")
    return render(request, 'contacts/create.html', {
        'form': form,
        'title': 'Add New Contact'
    })

@login_required
def contact_edit(request, contact_id):
    """
    View for editing an existing contact.
    """
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    
    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            
            logger.info(f"User {request.user.username} updated contact: {contact.name}")
            messages.success(request, f"Contact '{contact.name}' has been updated successfully.")
            return redirect('contacts:detail', contact_id=contact.id)
    else:
        form = ContactForm(instance=contact)
    
    logger.debug(f"Editing contact #{contact_id} for user: {request.user.username}")
    return render(request, 'contacts/edit.html', {
        'form': form,
        'contact': contact,
        'title': f'Edit {contact.name}'
    })

@login_required
def contact_delete(request, contact_id):
    """
    View for deleting a contact.
    """
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    
    if request.method == 'POST':
        contact_name = contact.name
        contact.delete()
        
        logger.info(f"User {request.user.username} deleted contact: {contact_name}")
        messages.success(request, f"Contact '{contact_name}' has been deleted.")
        return redirect('contacts:list')
    
    logger.debug(f"Confirming deletion of contact #{contact_id} for user: {request.user.username}")
    return render(request, 'contacts/delete.html', {
        'contact': contact,
        'title': f'Delete {contact.name}'
    }) 