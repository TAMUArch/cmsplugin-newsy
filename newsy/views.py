from datetime import date, timedelta

from django.contrib.auth.decorators import permission_required
from django.http import Http404, HttpResponseServerError
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.views.generic.list import ListView

from cms.utils import get_language_from_request

from newsy.models import NewsItem



def item_list(request, **kwargs):
    kwargs.setdefault('paginate_by', 25)
    kwargs.setdefault('filters', {})
    filters = kwargs.pop('filters')
    filters.setdefault('published', True)
    
    return ListView.as_view(queryset=NewsItem.site_objects.filter(**filters),
                            **kwargs)(request)

@permission_required('newsy.change_newsitem')
def upcoming_item_list(request, **kwargs):
    kwargs.setdefault('filters', {})
    kwargs['filters'].setdefault('published', False)
    return item_list(request, **kwargs)


def item_view(request, year, month, day, slug):
    try:
        page = NewsItem.objects.get(publication_date__year=year,
                                    publication_date__month=month,
                                    publication_date__day=day,
                                    slug=slug)
    except NewsItem.DoesNotExist, NewsItem.MultipleObjectsReturned:
        raise Http404()
    
    context = RequestContext(request)
    context['lang'] = get_language_from_request(request)
    context['current_page'] = page
    context['has_change_permissions'] = page.has_change_permission(request)
    return render_to_response(page.template, context)

@permission_required('newsy.change_newsitem')
def unpublished_item_view(request, slug):
    try:
        page = NewsItem.objects.get(published=False, slug=slug)
    except NewsItem.DoesNotExist:
        raise Http404()
    except NewsItem.MultipleObjectsReturned:
        raise HttpResponseServerError(u'Multiple unpublished items found with '
                                      'the slug: %s' % (slug,))
    
    if not page.has_change_permission(request):
        raise Http404()
    #request._current_page_cache = page
    context = RequestContext(request)
    context['lang'] = get_language_from_request(request)
    context['current_page'] = page
    context['has_change_permissions'] = page.has_change_permission(request)
    return render_to_response(page.template, context)

def archive_view(request, year, month=None, day=None, **kwargs):
    kwargs.setdefault('filters', {})
    kwargs['filters']['publication_date__year'] = year
    
    if day:
        kwargs['filters']['publication_date__day'] = day
    if month:
        kwargs['filters']['publication_date__month'] = month
    
    return item_list(request, **kwargs)