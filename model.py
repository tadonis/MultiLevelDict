class Level1Dict(object):
    """
    key should be string
    value should be numeric

    """
    size = 1
    level = 1

    def __init__(self, key, metric=None, value=None):
        self.key = key
        self.metric2value_dict = {metric: value} if metric and value else {}

    def get_value(self, metric):
        return self.metric2value_dict.get(metric, 0)

    @staticmethod
    def get_size():
        return 1

    def get_key(self):
        return self.key

    def add_metric(self, metric, value, is_value_accumulated=True):
        if is_value_accumulated:
            if metric in self.metric2value_dict:
                value += self.metric2value_dict.get(metric)
        self.metric2value_dict.update({metric: value})

    def get_metrics(self):
        return self.metric2value_dict.keys()

    def __repr__(self):
        return str({
            'key': self.key,
            'value': self.metric2value_dict
        })


class Level2Dict(object):
    level = 2

    def __init__(self, key, is_total_accumulated=True):
        self.key = key
        self.is_total_accumulated = is_total_accumulated
        self.sub_data = {}
        self.total = {}

    def add_sub_data(self, key, metric, count):
        if key in self.sub_data:
            self.sub_data[key].add_metric(metric, count)
        else:
            self.sub_data[key] = Level1Dict(key, metric, count)

        if self.is_total_accumulated:
            self.add_to_total(metric, count)

    def add_sub_level_data(self, level1_data):
        if level1_data.get_key() not in self.sub_data:
            self.sub_data[level1_data.get_key()] = level1_data
        else:
            for metric in level1_data.get_metrics():
                self.add_sub_data(level1_data.get_key(), metric, level1_data.get_value(metric))

    def add_total(self, metric, count):
        if self.is_total_accumulated:
            raise Exception("accumulated total cannot be set directly")
        self.total[metric] = count

    def add_to_total(self, metric, count):
        if metric in self.total:
            self.total[metric] += count
        else:
            self.total[metric] = count

    def get_sub_data(self, sub_key=None, cmp_func=None, sort_by_metric=None, reverse=True):
        if sub_key is None:
            if sort_by_metric:
                return sorted(self.sub_data.values(), key=lambda x: x.get_value(sort_by_metric), reverse=reverse)
            else:
                return sorted(self.sub_data.values(), cmp=cmp_func,
                              key=lambda x: x.get_key(), reverse=reverse)
        else:
            if not self.sub_data.get(sub_key):
                self.sub_data[sub_key] = Level1Dict(sub_key, self.is_total_accumulated)
            return self.sub_data.get(sub_key)

    def get_key(self):
        return self.key

    def get_total(self):
        return self.total

    def get_size(self):
        return sum(x.get_size() for x in self.sub_data.values())

    def __repr__(self):
        return str({
            'key': self.key,
            'value': self.sub_data,
            'total': self.total,
        })


class Level3Dict(object):
    level = 3

    def __init__(self, key, is_total_accumulated=True):
        self.key = key
        self.is_total_accumulated = is_total_accumulated
        self.sub_data = {}
        self.total = {}

    def add_sub_data(self, level1_key, level2_key, metric, count):
        if level1_key not in self.sub_data:
            self.sub_data[level1_key] = Level2Dict(level1_key, self.is_total_accumulated)

        self.sub_data[level1_key].add_sub_data(level2_key, metric, count)
        if self.is_total_accumulated:
            self.add_to_total(metric, count)

    def add_sub_level_data(self, level2_data):
        if level2_data.get_key() not in self.sub_data:
            self.sub_data[level2_data.get_key()] = level2_data
        else:
            for level1_data in level2_data.get_sub_data():
                self.sub_data[level2_data.get_key()].add_sub_level_data(level1_data)

    def add_total(self, metric, count):
        if self.is_total_accumulated:
            raise Exception("accumulated total cannot be set directly")
        self.total[metric] = count

    def add_to_total(self, metric, count):
        if metric in self.total:
            self.total[metric] += count
        else:
            self.total[metric] = count

    def get_sub_data(self, sub_key=None, cmp_func=None, sort_by_metric=None, reverse=True):
        if sub_key is None:
            if sort_by_metric:
                return sorted(self.sub_data.values(),
                              key=lambda x: x.get_total().get(sort_by_metric),
                              reverse=reverse)
            else:
                return sorted(self.sub_data.values(), cmp=cmp_func,
                              key=lambda x: x.get_key(), reverse=reverse)
        if not self.sub_data.get(sub_key):
            self.sub_data[sub_key] = Level2Dict(sub_key, self.is_total_accumulated)
        return self.sub_data.get(sub_key)

    def get_key(self):
        return self.key

    def get_total(self):
        return self.total

    def get_size(self):
        return sum(x.get_size() for x in self.sub_data.values())

    def __repr__(self):
        return str({
            'key': self.key,
            'value': self.sub_data,
            'total': self.total,
        })


class Level4Dict(object):
    level = 4

    def __init__(self, key, is_total_accumulated=True):
        self.key = key
        self.is_total_accumulated = is_total_accumulated
        self.sub_data = {}
        self.total = {}

    def add_sub_data(self, level1_key, level2_key, level3_key, metric, count):
        if level1_key not in self.sub_data:
            self.sub_data[level1_key] = Level3Dict(level1_key, self.is_total_accumulated)
        self.sub_data[level1_key].add_sub_data(level2_key, level3_key, metric, count)

        if self.is_total_accumulated:
            self.add_to_total(metric, count)

    def add_sub_level_data(self, level3_data):
        if level3_data.get_key() not in self.sub_data:
            self.sub_data[level3_data.get_key()] = level3_data
        else:
            for level2_data in level3_data.get_sub_data():
                self.sub_data[level3_data.get_key()].add_sub_level_data(level2_data)

    def add_total(self, metric, count):
        if self.is_total_accumulated:
            raise Exception("accumulated total cannot be set directly")
        self.total[metric] = count

    def add_to_total(self, metric, count):
        if metric in self.total:
            self.total[metric] += count
        else:
            self.total[metric] = count

    def get_sub_data(self, sub_key=None, cmp_func=None, sort_by_metric=None, reverse=True):
        if sub_key is None:
            if sort_by_metric:
                return sorted(self.sub_data.values(),
                              key=lambda x: x.get_total().get(sort_by_metric),
                              reverse=reverse)
            else:
                return sorted(self.sub_data.values(), cmp=cmp_func, key=lambda x: x.get_key(), reverse=reverse)
        if not self.sub_data.get(sub_key):
            self.sub_data[sub_key] = Level3Dict(sub_key, self.is_total_accumulated)
        return self.sub_data.get(sub_key)

    def get_key(self):
        return self.key

    def get_total(self):
        return self.total

    def get_size(self):
        return sum(x.get_size() for x in self.sub_data.values())

    def __repr__(self):
        return str({
            'key': self.key,
            'value': self.sub_data,
            'total': self.total,
        })
