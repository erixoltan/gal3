class A:
    self.Name = 'the name' # string
    def Bar(self, S, L):
        print('Bar')
class B(A):
    def Foo(self, X, Y):
        print('Foo')
# module: Classes
if __name__ == '__main__':
    First = A()
    Second = B()
    Second.Foo(1, 2)
    K = ['one', 'two', 'three']
    First.Bar('Hello', K)

