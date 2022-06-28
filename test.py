class Cat:
    MEOWS = 3

    def meow(self):
        for i in range(self.MEOWS):
            print("meow")


cat = Cat()
cat.meow()
