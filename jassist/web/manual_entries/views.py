from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import ManualEntry
from .forms import ManualEntryForm
import logging

logger = logging.getLogger(__name__)

@login_required
def create_entry(request):
    """
    View for creating a new manual entry.
    """
    if request.method == 'POST':
        form = ManualEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            logger.info(f"User {request.user.username} created a new {entry.classification} entry")
            messages.success(request, "Your entry has been saved successfully.")
            return redirect('manual_entries:list_entries')
    else:
        form = ManualEntryForm()
    
    logger.debug(f"Rendering create entry form for user: {request.user.username}")
    return render(request, 'manual_entries/create_entry.html', {
        'form': form,
        'title': 'Create New Entry'
    })

@login_required
def list_entries(request):
    """
    View for listing user's entries with pagination (15 entries per page).
    """
    entries = ManualEntry.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(entries, 15)  # Show 15 entries per page
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    logger.debug(f"Listing entries for user: {request.user.username}, page: {page_number}")
    return render(request, 'manual_entries/list_entries.html', {
        'page_obj': page_obj,
        'title': 'My Entries'
    })

@login_required
def edit_entry(request, entry_id):
    """
    View for editing an existing entry.
    """
    entry = get_object_or_404(ManualEntry, id=entry_id, user=request.user)
    
    if request.method == 'POST':
        form = ManualEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            logger.info(f"User {request.user.username} updated entry #{entry_id}")
            messages.success(request, "Your entry has been updated successfully.")
            return redirect('manual_entries:list_entries')
    else:
        form = ManualEntryForm(instance=entry)
    
    logger.debug(f"Editing entry #{entry_id} for user: {request.user.username}")
    return render(request, 'manual_entries/edit_entry.html', {
        'form': form,
        'entry': entry,
        'title': 'Edit Entry'
    })
