import sys, os, runpy, pickle
H = '/home/user/kaggle-qcircuit/supervisor_work/invsqrt'; sys.path.insert(0, H)
sys.path.insert(0, '/home/user/kaggle-qcircuit/data/kickmix')
import kickmix as km
Orig = km.CircuitBuilder
class B(Orig):
    def del_lookup(self, table=None, address=None, target=None, **kw):
        pickle.dump({'table': list(table), 'na': len(address), 'nt': len(target)}, open(os.environ['DUMP'], 'wb'))
        return super().del_lookup(table=table, address=address, target=target, **kw)
km.CircuitBuilder = B
sys.argv = ['lutpoly23.py'] + sys.argv[1:]
runpy.run_path(os.path.join(H, 'lutpoly23.py'), run_name='__main__')
