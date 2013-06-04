from copy import deepcopy
from logging import getLogger
import os.path

from django.conf import settings
from django.contrib import admin
from django.db import transaction
from django.forms import Widget, Textarea, CharField
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template.context import RequestContext
from django.template.defaultfilters import title, escape, force_escape, escapejs
from django.utils.decorators import method_decorator
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from cms.forms.widgets import PluginEditor
from cms.models import Placeholder, CMSPlugin
from cms.plugin_pool import plugin_pool
from cms.templatetags.cms_admin import admin_static_url
from cms.utils import cms_static_url
from cms.utils.conf import get_cms_setting
from cms.utils.helpers import make_revision_with_plugins
from cms.utils.placeholder import get_placeholder_conf
from cms.utils.plugins import get_placeholders, get_placeholders

from newsy.forms import NewsItemAddForm, NewsItemForm
from newsy.models import NewsItem, NewsItemThumbnail

if 'reversion' in settings.INSTALLED_APPS:
    _REVERSION = True
    from reversion import create_revision, set_user, set_comment
    from reversion.admin import VersionAdmin as ModelAdmin
    from reversion.models import Version
else:
    _REVERSION = False
    ModelAdmin = admin.ModelAdmin
    create_revision = lambda: lambda x: x



log = getLogger('newsy.admin')

method_require_POST = method_decorator(require_POST)

def get_template_from_request(request, obj=None, no_current_page=False):
    """
    Gets a valid template from different sources or falls back to the default
    template.
    """
    template = None
    if len(settings.NEWSY_TEMPLATES) == 1:
        return settings.NEWSY_TEMPLATES[0][0]
    if "template" in request.REQUEST:
        template = request.REQUEST['template']
    if not template and obj is not None:
        template = obj.get_template()
    if not template and not no_current_page and hasattr(request, "current_page"):
        current_page = request.current_page
        if hasattr(current_page, "get_template"):
            template = current_page.get_template()
    if template is not None and template in dict(settings.NEWSY_TEMPLATES).keys():
        return template    
    return settings.NEWSY_TEMPLATES[0][0]

def get_item_from_placeholder_if_exists(placeholder):
    try:
        return NewsItem.objects.get(placeholders=placeholder)
    except (Page.DoesNotExist, MultipleObjectsReturned,):
        return None


class NewsItemThumbnailAdmin(admin.TabularInline):
    model = NewsItemThumbnail
    extra=1
    max_num=1
    verbose_name=_('thumbnail')

class NewsItemAdmin(ModelAdmin):
    form = NewsItemForm
    inlines = [NewsItemThumbnailAdmin]
    date_hierarchy = 'publication_date'
    list_display = ['title', 'published', 'publication_date',]
    list_filter = ['published', 'template', ]
    search_fields = ('title', 'slug', 'short_title', 'page_title', 'description',)
    revision_form_template = "admin/newsy/newsitem/revision_form.html"
    recover_form_template = "admin/newsy/newsitem/recover_form.html"

    prepopulated_fields = {"slug": ("title",)}

    exclude = []

    add_fieldsets = [
        (None, {
            'fields': ['title', 'slug', 'description', 'sites',
                       'template'],
            'classes': ('general',),
        }),
    ]

    fieldsets = [
        (None, {
            'fields': ['title', 'short_title', 'page_title', 'description',
                       'published', 'tags'],
            'classes': ('general',),
        }),
        (_('Basic Settings'), {
            'fields': ['template'],
            'classes': ('low',),
            'description': _('Note: This page reloads if you change the selection. Save it first.'),
        }),
        (_('Sites'), {
            'fields': ['sites'],
            'classes': ('collapse',),
        }),
        (_('Advanced Settings'), {
            'fields': ['slug', 'publication_date'],
            'classes': ('collapse',),
        }),
    ]

    class Media:
        css = {
            'all': [cms_static_url(path) for path in (
                'css/rte.css',
                'css/pages.css',
                'css/change_form.css',
                'css/jquery.dialog.css',
            )]
        }
        js = ['%sjs/jquery.min.js' % admin_static_url()] + [cms_static_url(path) for path in (
            'js/plugins/admincompat.js',
            'js/libs/jquery.query.js',
            'js/libs/jquery.ui.core.js',
            'js/libs/jquery.ui.dialog.js',

        )]

    def get_urls(self):
        """Get the admin urls
        """
        from django.conf.urls.defaults import patterns, url
        info = "%s_%s" % (self.model._meta.app_label, self.model._meta.module_name)
        pat = lambda regex, fn: url(regex, self.admin_site.admin_view(fn), name='%s_%s' % (info, fn.__name__))

        url_patterns = patterns('',
            pat(r'add-plugin/$', self.add_plugin),
            pat(r'edit-plugin/([0-9]+)/$', self.edit_plugin),
            pat(r'remove-plugin/$', self.remove_plugin),
            pat(r'move-plugin/$', self.move_plugin),
            pat(r'^(?P<object_id>\d+)/change_template/$', self.change_template),
        )

        url_patterns = url_patterns + super(NewsItemAdmin, self).get_urls()
        return url_patterns

    def get_revision_instances(self, request, object):
        """ Return all the instances to be used in the object's revision """
        data = [object]
        filters = {'placeholder__newsitem': object }
        for plugin in CMSPlugin.objects.filter(**filters):
            data.append(plugin)
            plugin_instance, admin = plugin.get_plugin_instance()
            if plugin_instance:
                data.append(plugin_instance)
        return data

    @create_revision()
    def change_template(self, request, object_id):
        page = get_object_or_404(NewsItem, pk=object_id)
        if page.has_change_permission(request):
            to_template = request.POST.get("template", None)
            if to_template in dict(settings.NEWSY_TEMPLATES):
                page.template = to_template
                page.save()
                if "reversion" in settings.INSTALLED_APPS:
                    make_revision_with_plugins(page)
                return HttpResponse(str("ok"))
            else:
                return HttpResponseBadRequest("template not valid")
        else:
            return HttpResponseForbidden()

    """
    def get_formsets(self, request, obj=None):
        if obj:
            for inline in self.inline_instances:
                yield inline.get_formset(request, obj)
    """

    def get_fieldsets(self, request, obj=None):
        """
        Add fieldsets of placeholders to the list of already existing
        fieldsets.
        """

        if obj: # edit
            fieldsets = deepcopy(self.fieldsets)
            placeholders = get_placeholders(
                    get_template_from_request(request, obj))

            for placeholder in placeholders:
                name = get_placeholder_conf("name", placeholder, obj.template,
                        placeholder)
                name = _(name)
                fieldsets.append((title(name), {'fields': [placeholder],
                    'classes': ['plugin-holder']}))
        else: # new page
            fieldsets = deepcopy(self.add_fieldsets)

        return fieldsets

    def get_form(self, request, obj=None, **kwargs):
        """
        Get NewsItemForm for the NewsItem model and modify its fields depending 
        on the request.
        """
        if obj:
            form = super(NewsItemAdmin, self).get_form(request, obj, **kwargs)
            version_id = None
            versioned = False
            if "history" in request.path or 'recover' in request.path:
                versioned = True
                version_id = request.path.split("/")[-2]
            if settings.NEWSY_TEMPLATES:
                selected_template = get_template_from_request(request, obj)
                template_choices = list(settings.NEWSY_TEMPLATES)
                form.base_fields['template'].choices = template_choices
                form.base_fields['template'].initial = force_unicode(selected_template)

            placeholder_names = get_placeholders(selected_template)
            placeholders = {}

            # Load placeholder objects for all slots
            for placeholder_name in placeholder_names:
                placeholder, created = obj.placeholders.get_or_create(
                        slot=placeholder_name)
                placeholders.setdefault(placeholder.slot,
                        {})['object'] = placeholder

            if versioned:
                # Get the revision for the version id
                revision = get_object_or_404(Version, pk=version_id).revision

                plugins = []
                base_plugins = {}
                for version in revision.version_set.all():
                    try:
                        version = version.object_version.object
                        # Add base plugin to base plugins list
                        if version.__class__ == CMSPlugin:
                            base_plugins[version.pk] = version
                            continue
                        # Add plugin to plugins list
                        if isinstance(version, CMSPlugin):
                            plugins.append(version)
                    except models.FieldDoesNotExist:
                        # Model has changed since version was made
                        log.warning('Model has changed since version was made')
                        continue

                for plugin in plugins:
                    if plugin.pk in base_plugins:
                        plugin.placeholder = base_plugins[plugin.pk].placeholder
                        if base_plugins[plugin.pk].parent is None:
                            log.debug('Appending %s to %s' % (plugin,
                                plugin.placeholder.slot))
                            placeholder = placeholders.setdefault(plugin.placeholder.slot, {})
                            placeholder.setdefault('plugins', []).append(plugin)
            else:
                # If not versioned, load plugins for the slots
               for plugin in CMSPlugin.objects.filter(
                       placeholder__in=[p['object'] for p in
                           placeholders.itervalues()],
                       parent=None).order_by('position'):
                   placeholders[plugin.placeholder.slot].setdefault('plugins',
                           []).append(plugin)


            for placeholder_name in placeholder_names:
                installed_plugins = plugin_pool.get_all_plugins(
                        placeholder_name, obj)

                placeholder = placeholders.get(placeholder_name, {})
                if placeholder and 'object' in placeholder:
                    widget = PluginEditor(attrs={
                        'installed': installed_plugins,
                        'list': placeholder.get('plugins',[]),
                        'copy_languages': [],
                        'show_copy': False,
                        'language': 'en',
                        'placeholder': placeholder['object']
                    })

                    form.base_fields[placeholder_name] = CharField(widget=widget, required=False)
        else:
            self.inlines = []
            form = NewsItemAddForm
            form.base_fields['template'].initial = settings.NEWSY_TEMPLATES[0][0]

        return form

    def _get_site_languages(self, obj):
        return [('en', 'English')]

    def change_view(self, request, object_id, extra_context=None):
        """
        The 'change' admin view for the NewsItem model.
        """
        try:
            obj = self.model.objects.get(pk=object_id)
        except (self.model.DoesNotExist, ValueError,):
            # Don't raise Http404 just yet, because we haven't checked
            # permissions yet. We don't want an unauthenticated user to be able
            # to determine whether a given object exists.
            obj = None
        else:
            selected_template = get_template_from_request(request, obj)
            extra_context = {
                'placeholders': get_placeholders(selected_template),
                'page': obj,
                'ADMIN_MEDIA_URL': settings.ADMIN_MEDIA_PREFIX,
                'current_site_id': settings.SITE_ID,
                'language': 'en',
            }

        return super(NewsItemAdmin, self).change_view(request, object_id, extra_context)

    def revision_view(self, request, object_id, version_id, extra_context=None):
        if not self.has_change_permission(request, NewsItem.objects.get(pk=object_id)):
            raise PermissionDenied
        response = super(NewsItemAdmin, self).revision_view(request, object_id, version_id, extra_context)
        return response

    def history_view(self, request, object_id, extra_context=None):
        if not self.has_change_permission(request, NewsItem.objects.get(pk=object_id)):
            raise PermissionDenied
        return super(NewsItemAdmin, self).history_view(request, object_id, extra_context)

    def render_revision_form(self, request, obj, version, context, revert=False, recover=False):
        obj.version = version

        return super(NewsItemAdmin, self).render_revision_form(request, obj, version, context, revert, recover)

    @method_require_POST
    @xframe_options_sameorigin
    @create_revision()
    def add_plugin(self, request):
        """ Plugins can be added to an item or another plugin """
        # TODO: Enable number limitations from CMS placeholder configs

        if 'history' in request.path or 'recover' in request.path:
            return HttpResponseBadRequest("error")

        plugin_type = request.POST['plugin_type']
        placeholder_id = request.POST.get('placeholder', None)
        parent_id = request.POST.get('parent_id', None)

        if placeholder_id:
            placeholder = get_object_or_404(Placeholder, pk=placeholder_id)
            item = NewsItem.objects.get(placeholders=placeholder)
            if not item.has_change_permission(request):
                raise Http404
            plugin = CMSPlugin(language='en', plugin_type=plugin_type,
                    placeholder=placeholder, position=CMSPlugin.objects.filter(
                        placeholder=placeholder).count())
            plugin.save()
            if 'reversion' in settings.INSTALLED_APPS:
                set_user(request.user)
                set_comment(u'%(plugin_name)s plugin added to %(placeholder)s'
                        % {'plugin_name':
                            plugin_pool.get_plugin(plugin_type).name,
                            'placeholder': placeholder.slot})
        elif parent_id:
            parent = CMSPlugin.objects.select_related('placeholder').get(
                    pk=parent_id)
            item = NewsItem.objects.get(placeholders=parent.placeholder)
            if not item.has_change_permission(request):
                raise Http404
            plugin = CMSPlugin(language='en', plugin_type=plugin_type,
                    placeholder=parent.placeholder, parent=parent,
                    position=CMSPlugin.objects.filter(parent=parent).count())
            plugin.save()
            if 'reversion' in settings.INSTALLED_APPS:
                set_user(request.user)
                set_comment(u'%(plugin_name)s plugin added to plugin '
                        '%(plugin)s in %(placeholder)s' % {
                            'plugin_name':
                            plugin_pool.get_plugin(plugin_type).name,
                            'placeholder': parent.placeholder.slot,
                            'plugin': unicode(parent)})
        else:
            return HttpResponseBadRequest(
                    "Either parent of placeholder is required")

        return HttpResponse(unicode(plugin.pk), content_type='text/plain')

    @xframe_options_sameorigin
    @create_revision()
    def edit_plugin(self, request, plugin_id):
        plugin_id = int(plugin_id)
        recovery = 'history' in request.path or 'recover' in request.path
        if not recovery:
            plugin = get_object_or_404(
                    CMSPlugin.objects.select_related('placeholder'),
                    pk=plugin_id)
            item = NewsItem.objects.get(placeholders=plugin.placeholder)

            if not item.has_change_permission(request):
                raise Http404

            plugin_instance, plugin_admin = plugin.get_plugin_instance(self.admin_site)
        else:
            raise Exception('NEEDS WORK')
            """
            # history view with reversion
            pre_edit = request.path.split("/edit-plugin/")[0]
            version_id = pre_edit.split("/")[-1]
            Version.objects.get(pk=version_id)
            version = get_object_or_404(Version, pk=version_id)
            rev_objs = []
            for related_version in version.revision.version_set.all():
                try:
                    rev = related_version.object_version
                except models.FieldDoesNotExist:
                    continue
                else:
                    rev_objs.append(rev.object)
            # TODO: check permissions

            for obj in rev_objs:
                if obj.__class__ == CMSPlugin and obj.pk == plugin_id:
                    cms_plugin = obj
                    break
            inst, plugin_admin = cms_plugin.get_plugin_instance(self.admin_site)
            instance = None
            if cms_plugin.get_plugin_class().model == CMSPlugin:
                instance = cms_plugin
            else:
                for obj in rev_objs:
                    if hasattr(obj, "cmsplugin_ptr_id") and int(obj.cmsplugin_ptr_id) == int(cms_plugin.pk):
                        instance = obj
                        break
            if not instance:
                raise Http404("This plugin is not saved in a revision")
            """

        plugin_admin.cms_plugin_instance = plugin
        try:
            plugin_admin.placeholder = plugin.placeholder # TODO: what for reversion..? should it be inst ...?
        except Placeholder.DoesNotExist:
            pass

        if request.method == "POST":
            # set the continue flag, otherwise will plugin_admin make redirect to list
            # view, which actually does'nt exists
            request.POST['_continue'] = True

        if _REVERSION and recovery:
            # in case of looking to history just render the plugin content
            context = RequestContext(request)
            return render_to_response(plugin_admin.render_template,
                    plugin_admin.render(context, instance,
                        plugin_admin.placeholder))


        if not plugin_instance:
            # instance doesn't exist, call add view
            response = plugin_admin.add_view(request)
        else:
            # already saved before, call change view
            # we actually have the instance here, but since i won't override
            # change_view method, is better if it will be loaded again, so
            # just pass id to plugin_admin
            response = plugin_admin.change_view(request, unicode(plugin_id))

        if request.method == "POST" and plugin_admin.object_successfully_changed:
            # if reversion is installed, save version of the page plugins
            if _REVERSION and item:
                set_user(request.user)
                set_comment(_(u"%(plugin_name)s plugin edited at position "
                    "%(position)s in %(placeholder)s" % {
                        'plugin_name': plugin_pool.get_plugin(plugin.plugin_type).name,
                        'position': plugin.position,
                        'placeholder': plugin.placeholder.slot}))

            # read the saved object from plugin_admin - ugly but works
            saved_object = plugin_admin.saved_object

            context = {
                'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
                'plugin': saved_object,
                'is_popup': True,
                'name': unicode(saved_object),
                "type": saved_object.get_plugin_name(),
                'plugin_id': plugin_id,
                'icon': force_escape(escapejs(saved_object.get_instance_icon_src())),
                'alt': force_escape(escapejs(saved_object.get_instance_icon_alt())),
            }
            return render_to_response('admin/cms/page/plugin_forms_ok.html',
                    context, RequestContext(request))

        return response

    @method_require_POST
    @xframe_options_sameorigin
    @create_revision()
    def move_plugin(self, request):
        if 'history' in request.path:
            return HttpResponseBadRequest("Cannot move plugins in history view")

        # Moving a plugin to a new slot
        if 'plugin_id' in request.POST:
            plugin = CMSPlugin.objects.select_related(
                    'placeholder').get(pk=int(request.POST['plugin_id']))
            slot = request.POST['placeholder']

            item = NewsItem.objects.get(placeholders=plugin.placeholder)

            if slot not in get_placeholders(item.template):
                return HttpResponseBadRequest("Invalid target placeholder")

            placeholder = item.placeholders.get(slot=slot)

            plugin.placeholder = placeholder
            plugin.position = CMSPlugin.objects.filter(
                    placeholder=placeholder).count()
            plugin.parent = None
            plugin.save()

            for descendant in plugin.get_descendants():
                descendant.placeholder = placeholder
                descendant.save()

        # Reordering plugins in a slot
        if 'ids' in request.POST:
            plugin_ids = request.POST['ids'].split("_")
            item = None
            for position in range(0, len(plugin_ids)):
                plugin = CMSPlugin.objects.select_related(
                        'placeholder').get(pk=int(plugin_ids[position]))
                if item is None:
                    item = NewsItem.objects.get(
                            placeholders=plugin.placeholder)
                if plugin.position != position:
                    plugin.position = position
                    plugin.save()

        if item and _REVERSION:
            set_user(request.user)
            set_comment(_(u"Plugins where moved"))

        return HttpResponse(str("ok"))

    @method_require_POST
    @xframe_options_sameorigin
    @create_revision()
    def remove_plugin(self, request):
        if 'history' in request.path:
            return HttpResponseBadRequest('Invalid Request')

        plugin_id = int(request.POST['plugin_id'])
        plugin = get_object_or_404(
                CMSPlugin.objects.select_related('placeholder'), pk=plugin_id)
        item = NewsItem.objects.get(placeholders=plugin.placeholder)

        if not item.has_change_permission(request):
            return HttpResponseForbidden(
                    _("You do not have permission to remove a plugin"))

        plugin.delete()
        comment = "%(plugin_name)s plugin at position %(position)s in " \
                "%(placeholder)s was deleted." % {
                    'plugin_name': plugin_pool.get_plugin(
                        plugin.plugin_type).name,
                    'position': plugin.position,
                    'placeholder': plugin.placeholder}

        if _REVERSION:
            set_user(request.user)
            set_comment(comment)

        return HttpResponse("%s,%s" % (plugin_id, comment),
                content_type='text/plain')


admin.site.register(NewsItem, NewsItemAdmin)
