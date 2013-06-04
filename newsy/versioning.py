from cms.models.pluginmodel import CMSPlugin

from reversion import revision, revision_context_manager as context
from reversion.models import VERSION_CHANGE

from newsy.models import NewsItem



def make_revision_with_plugins(item, user=None, comment=None):
    assert isinstance(item, NewsItem)
    assert NewsItem in revision._registered_models

    if context.is_active():
        if user:
            context.set_user(user)
        if comment:
            context.set_comment(comment)
        adapter = revision.get_adapter(NewsItem)
        context.add_to_context(revision, item, adapter.get_version_data(item,
            VERSION_CHANGE))
        for plugin in CMSPlugin.objects.filter(placeholder__newsitem=item):
            plugin_instance, admin = plugin.get_plugin_instance()
            if plugin_instance:
                context.add_to_context(revision, plugin_instance,
                        revision.get_adapter(
                            plugin_instance.__class__).get_version_data(
                                plugin_instance, VERSION_CHANGE))
            context.add_to_context(revision, plugin, revision.get_adapter(
                plugin.__class__).get_version_data(plugin, VERSION_CHANGE))


