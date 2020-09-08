import torch
import random


def mask_init(self, num_train_per_class=20, num_val_per_class=30, seed=12345):
    num_nodes = self.data.y.size(0)
    self.train_mask = torch.zeros([num_nodes], dtype=torch.bool)
    self.val_mask = torch.zeros([num_nodes], dtype=torch.bool)
    self.test_mask = torch.ones([num_nodes], dtype=torch.bool)
    random.seed(seed)
    for c in range(self.num_classes):
        samples_idx = (self.data.y == c).nonzero().squeeze()
        perm = list(range(samples_idx.size(0)))
        random.shuffle(perm)
        perm = torch.as_tensor(perm).long()
        self.train_mask[samples_idx[perm][:num_train_per_class]] = True
        self.val_mask[samples_idx[perm][num_train_per_class:num_train_per_class + num_val_per_class]] = True
    self.test_mask[self.train_mask] = False
    self.test_mask[self.val_mask] = False


def mask_getitem(self, datum):
    datum.__setitem__("train_mask", self.train_mask)
    datum.__setitem__("val_mask", self.val_mask)
    datum.__setitem__("test_mask", self.test_mask)
    return datum


class StandardizeFeatures(object):
    r"""Row-normalizes node features to sum-up to one."""

    def __call__(self, data):
        mean_x = torch.mean(data.x, dim=0)
        std_x = torch.std(data.x, dim=0)
        data.x = (data.x - mean_x) / std_x
        return data

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)
