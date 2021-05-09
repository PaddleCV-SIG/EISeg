import yaml


class cfgData(object):
    def __init__(self, yaml_file):
        with open(yaml_file, 'r', encoding="utf-8") as f:
            fig_data = f.read()
            self.dicts = yaml.load(fig_data)

    def get(self, key):
        if key in self.dicts.keys():
            return self.dicts[key]
        else:
            raise ValueError('Not find this keyword.')


if __name__ == '__main__':
    cfg = cfgData('iann/train/train_config.yaml')
    print(cfg.get('use_vdl'))