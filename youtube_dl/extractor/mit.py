import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    clean_html,
    get_element_by_id,
)


class TechTVMITIE(InfoExtractor):
    IE_NAME = u'techtv.mit.edu'
    _VALID_URL = r'https?://techtv\.mit\.edu/(videos|embeds)/(?P<id>\d+)'

    _TEST = {
        u'url': u'http://techtv.mit.edu/videos/25418-mit-dna-learning-center-set',
        u'file': u'25418.mp4',
        u'md5': u'1f8cb3e170d41fd74add04d3c9330e5f',
        u'info_dict': {
            u'title': u'MIT DNA Learning Center Set',
            u'description': u'md5:82313335e8a8a3f243351ba55bc1b474',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        raw_page = self._download_webpage(
            'http://techtv.mit.edu/videos/%s' % video_id, video_id)
        clean_page = re.compile(u'<!--.*?-->', re.S).sub(u'', raw_page)

        base_url = self._search_regex(r'ipadUrl: \'(.+?cloudfront.net/)',
            raw_page, u'base url')
        formats_json = self._search_regex(r'bitrates: (\[.+?\])', raw_page,
            u'video formats')
        formats_mit = json.loads(formats_json)
        formats = [
            {
                'format_id': f['label'],
                'url': base_url + f['url'].partition(':')[2],
                'ext': f['url'].partition(':')[0],
                'format': f['label'],
                'width': f['width'],
                'vbr': f['bitrate'],
            }
            for f in formats_mit
        ]

        title = get_element_by_id('edit-title', clean_page)
        description = clean_html(get_element_by_id('edit-description', clean_page))
        thumbnail = self._search_regex(r'playlist:.*?url: \'(.+?)\'',
            raw_page, u'thumbnail', flags=re.DOTALL)

        return {'id': video_id,
                'title': title,
                'formats': formats,
                'description': description,
                'thumbnail': thumbnail,
                }


class MITIE(TechTVMITIE):
    IE_NAME = u'video.mit.edu'
    _VALID_URL = r'https?://video\.mit\.edu/watch/(?P<title>[^/]+)'

    _TEST = {
        u'url': u'http://video.mit.edu/watch/the-government-is-profiling-you-13222/',
        u'file': u'21783.mp4',
        u'md5': u'7db01d5ccc1895fc5010e9c9e13648da',
        u'info_dict': {
            u'title': u'The Government is Profiling You',
            u'description': u'md5:ad5795fe1e1623b73620dbfd47df9afd',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page_title = mobj.group('title')
        webpage = self._download_webpage(url, page_title)
        self.to_screen('%s: Extracting %s url' % (page_title, TechTVMITIE.IE_NAME))
        embed_url = self._search_regex(r'<iframe .*?src="(.+?)"', webpage,
            u'embed url')
        return self.url_result(embed_url, ie='TechTVMIT')

class OCWMITIE(InfoExtractor):
    IE_NAME = u'ocw.mit.edu'
    _VALID_URL = r'^http://ocw\.mit\.edu/courses/(?P<topic>[a-z0-9\-]+)'
    _BASE_URL = u'http://ocw.mit.edu/'

    _TESTS = [
        {
            u'url': u'http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-041-probabilistic-systems-analysis-and-applied-probability-fall-2010/video-lectures/lecture-7-multiple-variables-expectations-independence/',
            u'md5': u'348bef727b573c0bd9ad8a7c08c89ebd',
            u'info_dict': {
                u'title': u'7. Discrete Random Variables III',
                u'description': u'In this lecture, the professor discussed multiple random variables, expectations, and binomial distribution.',
                u'subtitles': u'http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-041-probabilistic-systems-analysis-and-applied-probability-fall-2010/video-lectures/lecture-7-multiple-variables-expectations-independence/MIT6_041F11_lec07_300k.mp4.srt'
            }
        },
        {
            u'url': u'http://ocw.mit.edu/courses/mathematics/18-01sc-single-variable-calculus-fall-2010/1.-differentiation/part-a-definition-and-basic-rules/session-1-introduction-to-derivatives/',
            u'md5': u'f4a434f08f15e581eb67cec0b57bcf6f',
            u'info_dict': {
                u'title': u'Lec 1 _ MIT 18.01 Single Variable Calculus, Fall 2007',
                u'subtitles': u'http://ocw.mit.edu//courses/mathematics/18-01sc-single-variable-calculus-fall-2010/ocw-18.01-f07-lec01_300k.SRT'
            }
        }
    ]

    def _real_extract(self, url):
        webpage = self._download_webpage(url, self.IE_NAME)
        title = self._html_search_meta(u'WT.cg_s', webpage)
        description = self._html_search_meta(u'Description', webpage)

        # search for call to ocw_embed_chapter_media(container_id, media_url, provider, page_url, image_url, start, stop, captions_file)
        embed_chapter_media = re.search(r'ocw_embed_chapter_media\((.+?)\)', webpage)
        if embed_chapter_media:
            metadata = re.sub(r'[\'"]', u'', embed_chapter_media.group(1))
            metadata = re.split(r', ?', metadata)
            yt = metadata[1]
            subs = compat_urlparse.urljoin(self._BASE_URL, metadata[7])
        else:
            # search for call to ocw_embed_chapter_media(container_id, media_url, provider, page_url, image_url, captions_file)
            embed_media = re.search(r'ocw_embed_media\((.+?)\)', webpage)
            if embed_media:
                metadata = re.sub(r'[\'"]', u'', embed_media.group(1))
                metadata = re.split(r', ?', metadata)
                yt = metadata[1]
                subs = compat_urlparse.urljoin(self._BASE_URL, metadata[5])
            else:
                raise ExtractorError('Unable to find embedded YouTube video.')

        data = self.url_result(yt, 'Youtube')
        data['subtitles'] = subs
        
        return data
