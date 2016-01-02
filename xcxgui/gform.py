import urllib
import urllib2


def get_ip():
  header = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)'}
  req = urllib2.Request('http://ipchicken.com', None, header)
  f = urllib2.urlopen(req)
  htm = f.read()
  prefix = '<p align="center"><font face="Verdana, Arial, Helvetica, sans-serif" size="5" color="#0000FF"><b>'
  suffix = '<A HREF="javascript:makeLink()"><font size="2">Add to Favorites</font></A>'
  prefix_idx = htm.find(prefix)
  suffix_idx = htm.find(suffix, prefix_idx)
  if prefix_idx < 0 or suffix_idx < 0:
    raise SyntaxError('failed to parse ipchicken.com response')
  return htm[prefix_idx+len(prefix):suffix_idx-6].strip() # also remove " <br>\r\n"


def gform_submit_item_name(type_str, id_str, name, contributor):
  ip = get_ip()
  header = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)'}
  url = "https://docs.google.com/forms/d/1SpklxDXV-rxhPNmlQn8f9CIYknVBfKt7qPjgEDtQGmE/formResponse"
  values = {'entry.830127543': str(type_str), # type
            'entry.1526725833': str(id_str), # id
            'entry.1760003305': str(name), # name
            'entry.1969796457': str(contributor), # contributor
            'entry.252943852': ip, # ip
            'draftResponse':"[]",
            'pageHistory':"0"}
  data = urllib.urlencode(values)
  req = urllib2.Request(url, data, header)
  f = urllib2.urlopen(req)
  res = f.read()
  if res.find('<title>Thanks!</title>') < 0:
    raise SyntaxError('invalid form data')
