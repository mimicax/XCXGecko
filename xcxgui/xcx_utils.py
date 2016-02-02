import ConfigParser

from gui.gecko_utils import DataStore
from item_utils import *


class XCXDataStore(DataStore):
  def __init__(self):
    super(XCXDataStore, self).__init__()
    self.item_ids = dict()
    self.gear_ids = dict()
    self.item_lines = []
    self.item_types = []

  def parseCfg(self, path):
    items = [('General', 'wiiu_ip', 'wiiu_ip'),
             ('General', 'loadiine_v4_pygecko', 'loadiine_v4_pygecko'),
             ('Databases', 'code_db', 'code_db'),
             ('Databases', 'item_id_db', 'item_id_db'),
             ('Databases', 'gear_id_db', 'gear_id_db'),
             ('Databases', 'local_code_db', 'local_code_db'),
             ('Databases', 'local_item_id_db', 'local_item_id_db'),
             ('Databases', 'local_gear_id_db', 'local_gear_id_db'),
             ('Verbosity', 'read', 'verbose_read'),
             ('Verbosity', 'poke', 'verbose_poke'),
             ('Verbosity', 'poke_str', 'verbose_poke_str')]

    config = dict()
    try:
      cfg = ConfigParser.RawConfigParser()
      cfg.read(path)
      for section, option, label in items:
        config[label] = cfg.get(section, option)
    except BaseException, e:
      traceback.print_exc()
      raise SyntaxError('Failed to parse %s: %s' % (path, str(e)))
    config['loadiine_v4_pygecko'] = (config['loadiine_v4_pygecko'] == 'True')
    config['verbose_read'] = (config['verbose_read'] == 'True')
    config['verbose_poke'] = (config['verbose_poke'] == 'True')
    config['verbose_poke_str'] = (config['verbose_poke_str'] == 'True')
    self.config = config
