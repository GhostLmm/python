# encoding: utf-8
__author__ = 'zhanghe'

import random
import math


class UserBasedCF:
    """
    基于用户的协同过滤算法
    """
    def __init__(self, datafile=None):
        self.user_sim_best = dict()  # 优化后的用户相似度集合
        self.user_sim = dict()  # 用户相似度集合
        self.train_data = {}  # 用户-物品的评分表
        self.test_data = {}  # 测试集
        self.data = []
        self.datafile = datafile
        self.read_data()
        self.split_data(3, 47)

    def read_data(self, datafile=None):
        """
        读取数据文件
        """
        self.datafile = datafile or self.datafile
        for line in open(self.datafile):
            user_id, item_id, record, _ = line.split()
            self.data.append((user_id, item_id, int(record)))

    def split_data(self, k, seed, data=None, m=8):
        """
        拆分数据集为两部分：测试集合，训练集合
        split the data set
        test_data is a test data set
        train_data is a train set
        test data set / train data set is 1:M-1
        """
        data = data or self.data
        random.seed(seed)
        for user, item, record in self.data:
            if random.randint(0, m) == k:
                self.test_data.setdefault(user, {})
                self.test_data[user][item] = record
            else:
                self.train_data.setdefault(user, {})
                self.train_data[user][item] = record

    def user_similarity(self, train=None):
        """
        用户相似度矩阵
        基于余弦相似度
        One method of getting user similarity matrix
        """
        train = train or self.train_data
        for u in train.keys():
            for v in train.keys():
                if u == v:
                    continue
                self.user_sim.setdefault(u, {})
                self.user_sim[u][v] = len(set(train[u].keys()) & set(train[v].keys()))
                self.user_sim[u][v] /= math.sqrt(len(train[u]) * len(train[v]) * 1.0)

    def user_similarity_best(self, train=None):
        """
        优化后的用户相似度矩阵
        the other method of getting user similarity which is better than above
        you can get the method on page 46
        In this experiment，we use this method
        """
        train = train or self.train_data
        item_users = dict()  # 所有训练集合中的物品-用户集合
        for u, item in train.items():
            for i in item.keys():
                item_users.setdefault(i, set())
                item_users[i].add(u)  # item_users[物品] = [用户1,用户2,用户3……]
        user_item_count = dict()  # 单个用户评价的物品数量
        count = dict()  # 用户-用户之间评价相同物品数量矩阵
        # 遍历所有被用户评价过的物品及对应的用户
        for item, users in item_users.items():
            # 遍历某个物品下所有评价过的用户
            for u in users:
                user_item_count.setdefault(u, 0)
                user_item_count[u] += 1
                for v in users:
                    if u == v:
                        continue
                    count.setdefault(u, {})
                    count[u].setdefault(v, 0)
                    count[u][v] += 1
        for u, related_users in count.items():
            self.user_sim_best.setdefault(u, dict())
            for v, cuv in related_users.items():
                self.user_sim_best[u][v] = cuv / math.sqrt(user_item_count[u] * user_item_count[v] * 1.0)

    def recommend(self, user, train=None, k=8, n_item=40):
        """
        推荐
        """
        train = train or self.train_data
        rank = dict()  # 排序
        interacted_items = train.get(user, {})  # 获取指定用户下所有的物品-评分信息
        # 遍历相似度最高的前k个用户相似度集合
        for v, wuv in sorted(self.user_sim_best[user].items(), key=lambda x: x[1], reverse=True)[0:k]:
            # 遍历这k个用户下所有的物品-评分信息
            for i, rvi in train[v].items():
                if i in interacted_items:
                    continue  # 跳过这个用户存在的物品
                rank.setdefault(i, 0)
                rank[i] += wuv  # 当前用户相关物品-相似度之和
        # 返回相似度之和最高的前n_item个物品-相似度集合
        return dict(sorted(rank.items(), key=lambda x: x[1], reverse=True)[0:n_item])

    def recall_and_precision(self, train=None, test=None, k=8, n_item=10):
        """
        召回率和准确率
        train为训练集合，test为验证集合，给每个用户推荐n_item个物品
        Get the recall and precision, the method you want to know is listed
        in the page 43
        """
        train = train or self.train_data
        test = test or self.test_data
        hit = 0
        recall = 0
        precision = 0
        for user in train.keys():  # 遍历每个用户训练集合
            tu = test.get(user, {})
            rank = self.recommend(user, train=train, k=k, n_item=n_item)
            for item, _ in rank.items():
                if item in tu:  # 如果某用户推荐的物品在他的测试集合中
                    hit += 1  # 推荐正确的数量
            recall += len(tu)  # 所有测试的数量
            precision += n_item  # 所有推荐的数量
        return hit / (recall * 1.0), hit / (precision * 1.0)

    def coverage(self, train=None, test=None, k=8, n_item=10):
        """
        覆盖率
        """
        train = train or self.train_data
        test = test or self.test_data
        recommend_items = set()  # 被推荐的物品集合
        all_items = set()  # 所有训练的物品集合
        for user in train.keys():
            for item in train[user].keys():
                all_items.add(item)
            rank = self.recommend(user, train, k=k, n_item=n_item)
            for item, _ in rank.items():
                recommend_items.add(item)
        return len(recommend_items) / (len(all_items) * 1.0)

    def popularity(self, train=None, test=None, k=8, n_item=10):
        """
        流行度
        Get the popularity
        the algorithm on page 44
        """
        train = train or self.train_data
        test = test or self.test_data
        item_popularity = dict()  # 物品流行次数集合
        for user, items in train.items():
            for item in items.keys():
                item_popularity.setdefault(item, 0)
                item_popularity[item] += 1  # 训练集合中某个物品出现的次数之和作为该物品流行次数
        ret = 0  # 流行度结果
        n = 0  # 推荐的总个数
        for user in train.keys():
            rank = self.recommend(user, train, k=k, n_item=n_item)  # 获得推荐结果
            for item, _ in rank.items():
                ret += math.log(1 + item_popularity[item])  # (流行次数+1)>=1的自然对数(结果>=0)
                n += 1
        return ret / (n * 1.0)


def test_user_based_cf():
    """
    测试基于用户的协同过滤不同k值下的推荐评测指标
    """
    ub_cf = UserBasedCF('u.data')
    ub_cf.user_similarity_best()
    print "%3s%20s%20s%20s%20s" % ('K', 'recall', 'precision', 'coverage', 'popularity')
    for k in [5, 10, 20, 40, 80, 160]:
        recall, precision = ub_cf.recall_and_precision(k=k)
        coverage = ub_cf.coverage(k=k)
        popularity = ub_cf.popularity(k=k)
        print "%3d%19.3f%%%19.3f%%%19.3f%%%20.3f" % (k, recall * 100, precision * 100, coverage * 100, popularity)


def test_recommend():
    """
    通过测试集合分别测试不同K值的推荐情况
    """
    ub_cf = UserBasedCF('u.data')
    ub_cf.user_similarity_best()
    user = '345'
    for k in [5, 10, 20, 40, 80, 160]:
        rank = ub_cf.recommend(user, train=None, k=k, n_item=5)
        print "%s [user=%5s  K=%3s] %s" % ('-'*12, user, k, '-'*12)
        print "%5s%20s%20s" % ('item', 'similarity', 'record')
        for i, rvi in rank.items():
            items = ub_cf.test_data.get(user, {})
            record = items.get(i, 0)
            print "%5s%20.4f%20.4f" % (i, rvi, record)


if __name__ == "__main__":
    # test_user_based_cf()
    test_recommend()


"""
数据集：
下载链接：http://grouplens.org/datasets/movielens/
这里测试使用的是 [ml-100k.zip](http://files.grouplens.org/datasets/movielens/ml-100k.zip)
$ wc -l u.data
100000 u.data

推荐评测指标测试结果：
  K              recall           precision            coverage          popularity
  5             14.148%             16.554%             39.940%               5.230
 10             16.777%             19.629%             31.084%               5.367
 20             18.309%             21.421%             24.518%               5.469
 40             19.333%             22.619%             18.675%               5.552
 80             19.161%             22.418%             14.518%               5.614
160             18.291%             21.400%             11.807%               5.660

设定不同的k值重新进行训练，最后取误差率最小的k值

推荐情况测试结果：
------------ [user=  345  K=  5] ------------
 item          similarity              record
   98              2.2329              5.0000
  496              2.2329              0.0000
  196              2.2329              5.0000
   97              2.2329              0.0000
   96              2.2329              0.0000
------------ [user=  345  K= 10] ------------
 item          similarity              record
   98              4.2893              5.0000
  117              4.2893              4.0000
  196              4.2893              5.0000
  181              3.8813              4.0000
    8              3.8813              0.0000
------------ [user=  345  K= 20] ------------
 item          similarity              record
   98              8.2600              5.0000
  117              8.2600              4.0000
  181              7.8520              4.0000
  423              7.4183              0.0000
   97              7.4501              0.0000
------------ [user=  345  K= 40] ------------
 item          similarity              record
   98             14.7372              5.0000
  117             14.3565              4.0000
  181             14.3126              4.0000
  196             13.1593              5.0000
  423             13.5466              0.0000
------------ [user=  345  K= 80] ------------
 item          similarity              record
   98             25.5408              5.0000
  117             24.8100              4.0000
  181             25.4284              4.0000
  173             21.9982              5.0000
  423             24.0058              0.0000
------------ [user=  345  K=160] ------------
 item          similarity              record
    1             37.6008              3.0000
   98             43.0039              5.0000
  423             41.4776              0.0000
  181             42.5909              4.0000
  117             40.6466              4.0000



参考链接：
[推荐系统学习：协同过滤实现](http://wuchong.me/blog/2014/04/19/recsys-cf-study/)
[基于用户的协同过滤算法](http://www.oschina.net/code/snippet_244322_15369)
"""