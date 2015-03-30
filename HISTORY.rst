1.2 (2015/03/30)
----------------

* use short title in cascade rss

1.1 (2015/03/05)
----------------

* banner jpg size, 25 items for cascade rss

1.0 (2015/03/04)
----------------

* added carousel and thumbnail to cascade rss

0.9 (2015/03/03)
----------------

* Added cascade rss urls with enclosure

0.8 (2015/02/23)
----------------

* Started adding enclosure in rss

0.7b7 (2014/02/25)
------------------

* Added external link field

0.7b6 (2013/07/25)
------------------

* Removed extra logging output

0.7b5 (2013/07/25)
------------------

* Bugfix for admin view of news item with thumbnail inline
* Bugfix for 404's on news item view

0.7b4 (2013/07/02)
------------------

* Adding plugin admin view doesn't generate 500 errors when a placeholder_id 
  isn't valid
* Added version numbers to javascript in template to help with caching issues

0.7b3 (2013/06/25)
------------------

* Added a monkeypatch for permissions checking on CMS Placeholders

0.7b2 (2013/06/07)
------------------

* Bugfix: getting placeholder configuration for new CMS

0.7b1 (2013/06/07)
------------------

* Cleaning and upgrading of the Admin integration
* Reversion now saves plugins with revisions properly
* Removed remaining multi-lingual code as it was not supported or working

0.7a1 (2013/05/06)
------------------

* Reversion fixes for reversion 1.7
* Requires django-cms >= 2.4.1
* Requires django-photologue >= 2.5

0.6.1 (2012/07/30)
------------------

* Fixed a typo bug in the item view

0.6 (2012/06/15)
----------------

* Added a tags view
* Added support for tags with dashes
* Added a CMS Attach Menu for menu/breadcrumb integration
* Added year/month/day values to context when viewing news items with those
  filters applied

0.5.1 (2012/06/04)
------------------

* Added a null log handler
* Switch Tag Field to a Text based field to allow for more tags per item

0.5 (2012/06/01)
----------------

* Fixed the bug when moving plugins between placeholders (Github issue #15)
* Fixed page title when editing a news item (Github issue #17)
* Site selection is now a multi-checkbox input (Github issue #18)
* Fixed reversion integration (Github issue #19)
* Added a redirect to handle a changed publication date with a unique slug
  (Github issue #16)

0.4.1 (2011/12/08)
------------------

* Added debug logging output

0.4 (2011/10/12)
----------------

* Added a latest news plugin

0.3 (2011/10/12)
----------------

* Switched to using the class based generic list view properly
* Added tag browsing support
* Added default pagination on list views of 30 (when using shortcut views)
* Added some new methods to the NewsItem model to make a few things easier
* Method for getting tag and date filters in generic view
* Added ampersands to allowed tag characters (urls.py)
* Reorganized form fields and increased the size of the title fields and tag field
* News item slugs must be lowercase
* Added the 0003 data migration to lowercase existing slugs
* Added get_next_published and get_previous_published methods to news item
* Added RSS feed for all published and for all tags (one feed per tag)

0.2 (2011/07/25)
----------------

* Added an archive view (GitHub issue #10)
* Added tags field to NewsItem model for admin integration (GitHub issue #7)
* Added tags field to NewsItem administration (GitHub issue #7)
* Added south migration for the tags field (GitHub issue #7)
* Added a news_plugins_media tag for rendering plugin media links (GitHub issue #8)
* Added a site_objects model manager to news item (GitHub issue #11)
* Modified list views to use the site_objects model manager (GitHub issue #11)
* Added permission wrapper around list view and news item view for unpublished 
  items (GitHub issue #12)

0.1 (2011/07/15)
----------------

* A very basic, working version for demonstration
