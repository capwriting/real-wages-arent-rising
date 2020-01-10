# Works for any CPS data January 1998 to December 2002
# Spreadsheet uses data from http://thedataweb.rm.census.gov/pub/cps/basic/199801-/apr98pub.zip
# and http://thedataweb.rm.census.gov/pub/cps/basic/199801-/apr01pub.zip
# Output is valid csv; Can be viewed in excel, etc. by saving output as a csv file

class cps_person:
    age = 0
    child_value = 0

    def __init__(self, new_age, new_child_value):
        self.age = new_age
        self.child_value = new_child_value


class cps_household:
    hhuid = None
    members = []
    num_members = 0

    def __init__(self, new_hhuid):
        self.hhuid = new_hhuid
        self.num_members = 0
        self.members = []

    def set_num_members(self, new_num_members):
        self.num_members = new_num_members

    def add_person(self, age, child_value):
        self.members.append(cps_person(age, child_value))

    def pass_integrity_checks(self):
        checks_pass = True
        if self.num_members != len(self.members):
            print ('{0},num_household_mismatch,{1},{2}'.format(self.hhuid, self.num_members, len(self.members)))
            checks_pass = False
        if self.num_adults <= 0 and self.num_children != 0:
            print ('{0},children_only_household,{1},{2}.'.format(self.hhuid, self.num_adults, self.num_children))
            checks_pass = False
        for member in self.members:
            if member.age >= 18 and member.child_value == 1:
                print('{0},child_bad_age,{1}'.format(self.hhuid, member.age))
                checks_pass = False

    def children_composition(self, max_length=9999):
        child_string = '{0}{1}{2}{3}'.format(self.num_infants * 'I', self.num_preschoolers * 'P', self.num_schoolage * 'S', self.num_teenagers * 'T')
        if len(child_string) > max_length:
            return child_string[0:max_length] + "M"
        else:
            return child_string

    @property
    def num_adults(self):
        adults_count = 0
        for member in self.members:
            if member.age >= 18:
                adults_count += 1
        return adults_count

    @property
    def num_children(self):
        children_count = 0
        for member in self.members:
            if member.age < 18:
                children_count += 1
        return children_count

    @property
    def num_infants(self):
        infants_count = 0
        for member in self.members:
            if member.age <= 2:
                infants_count += 1
        return infants_count

    @property
    def num_preschoolers(self):
        preschoolers_count = 0
        for member in self.members:
            if member.age >= 3 and member.age <= 5:
                preschoolers_count += 1
        return preschoolers_count

    @property
    def num_schoolage(self):
        schoolage_count = 0
        for member in self.members:
            if member.age >= 6 and member.age <= 12:
                schoolage_count += 1
        return schoolage_count

    @property
    def num_teenagers(self):
        teenager_count = 0
        for member in self.members:
            if member.age >= 13 and member.age <= 17:
                teenager_count += 1
        return teenager_count



class categories:
    categories = {}
    sanitized_categories = {}
    allowed_num_adults = 0
    allowed_num_children = 0

    def __init__(self, *, max_num_adults, max_num_children):
        self.categories = {}
        self.santizied_categories = {}
        self.allowed_num_adults = max_num_adults
        self.allowed_num_children = max_num_children

    def add_household(self, household):
        label = self._generate_label(household)
        sanitized_label = self._generate_sanitized_label(household)

        if label not in self.categories.keys():
            self.categories[label] = 1
        else:
            self.categories[label] += 1
        
        if sanitized_label not in self.sanitized_categories.keys():
            self.sanitized_categories[sanitized_label] = 1
        else:
            self.sanitized_categories[sanitized_label] += 1


    def _generate_label(self, household):
        return '{0}A{1}'.format(household.num_adults, household.children_composition())

    def _generate_sanitized_label(self, household):
        if household.num_adults <= self.allowed_num_adults:
            return '{0}A{1}'.format(household.num_adults, household.children_composition(self.allowed_num_children))
        elif household.num_adults == 0 and household.num_children == 0:
            return 'No Ans.'
        else:
            return 'MA{0}'.format(household.children_composition(self.allowed_num_children))


# Change the below line to match the filename you want to process
with open('apr01pub.cps') as f:
    rawdata = f.readlines()

compiled_data = {}

for row in rawdata:
    current_hhuid = row[0:15] + row[74:76]
    current_age = int(row[121:123])
    if current_age == -1:
        continue
    current_num_household = int(row[58:60])
    current_person_type = int(row[160:162])

    if not current_hhuid in compiled_data.keys():
        compiled_data[current_hhuid] = cps_household(current_hhuid)

    compiled_data[current_hhuid].set_num_members(current_num_household)
    compiled_data[current_hhuid].add_person(current_age, current_person_type)

# Here you can set the allowed number of adults and children
# Anything not allowed will be collapsed into "other" categories
groups = categories(max_num_adults=2, max_num_children=3)
total_adults = 0
total_infants = 0
total_preschoolers = 0
total_schoolage = 0
total_teenagers = 0

print ("HHUID,Adults,Children")
for hhuid, household in compiled_data.items():
    print ("{0},{1},{2}".format(household.hhuid, household.num_adults, household.children_composition()))
    total_adults += household.num_adults
    total_infants += household.num_infants
    total_preschoolers += household.num_preschoolers
    total_schoolage += household.num_schoolage
    total_teenagers += household.num_teenagers
    groups.add_household(household)


# Error check
print(',')
print ("HHUID,Error Type,Num Found,Num Expected")
for hhuid, household in compiled_data.items():
    household.pass_integrity_checks()


# Summary output
print(",,")
print("Adults/Children,Number")

for i in sorted(groups.categories):
    print('{0},{1}'.format(i, groups.categories[i]))
print('Total,{0}'.format(len(compiled_data)))
print('Average Adults,{0}'.format(total_adults/len(compiled_data)))
print('Average Infants,{0}'.format(total_infants/len(compiled_data)))
print('Average Preschoolers,{0}'.format(total_preschoolers/len(compiled_data)))
print('Average Schoolage,{0}'.format(total_schoolage/len(compiled_data)))
print('Average Teenagers,{0}'.format(total_teenagers/len(compiled_data)))

# Generate a cleaner output, with outliers collapsed into "More" categories
print(",,")
print("Adults/Children,Number,Weight")

test_total = 0

for i in sorted(groups.sanitized_categories):
    print('{0},{1}'.format(i, groups.sanitized_categories[i]))
print('Total,{0}'.format(len(compiled_data)))

# Generate an organized output that I can copy directly into google sheets
one_child_series = ['I', 'P', 'S', 'T']
two_child_series = ['II', 'IP', 'IS', 'IT', 'PP', 'PS', 'PT', 'SS', 'ST', 'TT']
three_child_series = ['III', 'IIP', 'IIS', 'IIT', 'IPP', 'IPS', 'IPT', 'ISS', 'IST', 'ITT', 'PPP', 'PPS', 'PPT', 'PSS', 'PST', 'PTT', 'SSS', 'SST', 'STT', 'TTT']
labels = {}

# Generate all possible labels
for adults in ['0', '1', '2', '3', 'M']:
    if adults != '0':
        labels['{0}A'.format(adults)] = 0
        if '{0}A'.format(adults) in groups.sanitized_categories.keys():
            labels['{0}A'.format(adults)] = groups.sanitized_categories['{0}A'.format(adults)]
    for child in one_child_series:
        labels['{0}A{1}'.format(adults, child)] = 0
        if '{0}A{1}'.format(adults, child) in groups.sanitized_categories.keys():
            labels['{0}A{1}'.format(adults, child)] = groups.sanitized_categories['{0}A{1}'.format(adults, child)]
    for child in two_child_series:
        labels['{0}A{1}'.format(adults, child)] = 0
        if '{0}A{1}'.format(adults, child) in groups.sanitized_categories.keys():
            labels['{0}A{1}'.format(adults, child)] = groups.sanitized_categories['{0}A{1}'.format(adults, child)]
    for child in three_child_series:
        labels['{0}A{1}'.format(adults, child)] = 0
        if '{0}A{1}'.format(adults, child) in groups.sanitized_categories.keys():
            labels['{0}A{1}'.format(adults, child)] = groups.sanitized_categories['{0}A{1}'.format(adults, child)]
    for child in three_child_series:
        labels['{0}A{1}M'.format(adults, child)] = 0
        if '{0}A{1}M'.format(adults, child) in groups.sanitized_categories.keys():
            labels['{0}A{1}M'.format(adults, child)] = groups.sanitized_categories['{0}A{1}M'.format(adults, child)]

top_row = []
bottom_row = []
for label, value in labels.items():
    top_row.append(label)
    bottom_row.append(str(value))

print(','.join(top_row))
print(','.join(bottom_row))
print('Total,{0}'.format(len(compiled_data)))