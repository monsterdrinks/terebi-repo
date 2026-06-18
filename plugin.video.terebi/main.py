import sys
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

# Import our custom scraper
from resources.lib import scraper

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')

def build_url(query):
    base_url = sys.argv[0]
    return base_url + '?' + urllib.parse.urlencode(query)

def list_channels():
    # Get channels from scraper
    channels = scraper.get_channels()
    
    # Get the plugin handle
    handle = int(sys.argv[1])
    
    for channel in channels:
        # Create a list item
        list_item = xbmcgui.ListItem(label=channel['name'])
        list_item.setInfo('video', {'title': channel['name'], 'mediatype': 'video'})
        
        # Add artwork/logos
        if 'logo' in channel:
            list_item.setArt({'thumb': channel['logo'], 'icon': channel['logo'], 'poster': channel['logo']})
            
        list_item.setProperty('IsPlayable', 'true')
        
        # Build the URL to our addon that handles the 'play' action
        url = build_url({'action': 'play', 'video_url': channel['url']})
        
        # Add item to the directory
        xbmcplugin.addDirectoryItem(handle=handle, url=url, listitem=list_item, isFolder=False)
        
    # Finish creating the directory
    xbmcplugin.endOfDirectory(handle)

def play_video(video_url):
    # Get the final stream URL and the required referer
    m3u8_url, referer = scraper.get_stream_url(video_url)
    
    if m3u8_url:
        # Append the Referer header to the URL so Kodi's player sends it when fetching the chunks
        play_path = m3u8_url
        if referer:
            play_path += f"|Referer={referer}"
            
        # Create a playable list item
        play_item = xbmcgui.ListItem(path=play_path)
        
        # Pass it back to Kodi to play
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, play_item)
    else:
        xbmcgui.Dialog().notification(ADDON_NAME, "Failed to extract stream URL", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem())

def router(paramstring):
    # Parse the query parameters
    params = dict(urllib.parse.parse_qsl(paramstring))
    
    action = params.get('action')
    
    if action == 'play':
        # Play the video
        play_video(params.get('video_url'))
    else:
        # Default action: list channels
        list_channels()

if __name__ == '__main__':
    # Call the router function and pass the parameters
    # sys.argv[2] contains the query string (e.g. ?action=play&video_url=...)
    router(sys.argv[2][1:])
