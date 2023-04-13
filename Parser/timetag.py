'''
Timetag is a tag that is extracted from the NEWS documents. 
Each timetag contains the weight and the values of the tag itself.
'''

#The class for the timetag object
class TimeTag:
    def __init__(self, date, count):
        # The date or the value of the tag itself
        self.date = date
        # The texttype which would be either the header, summary or details. Weight is based on this.
        # self.textType = textType
        # # Appearence is the position of the number of bytes from the start of the article where the tag first appears
        # self.appearence = appearence
        # Count is the number of unique times the tag appears in the article
        self.count = count
        # The weight assigned to each tag. Weight specifies how much of a good focus time it is. The higher the weight, the better.
        self.weight = count

    # To print the tag for logging purposes
    def __repr__(self):
        # print({"date": self.date, "weight": self.weight, "count": self.count})
        return f'date: {self.date}, weight: {self.weight}, count: {self.count}'

