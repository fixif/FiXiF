#coding=utf8

class FIPLabel(object):
    
    """
    This class is used to label objects, that can be indexed in a FIPindex
    """
    
    is_debug_print = True # print label at end of __init__
    
    # Contains subclass:free_num items
    free_num = {}

    def __repr__(self):
        
        fmt = '{0:20} = {1:20} \n'
        
        str_repr = ''
        
        str_repr += fmt.format('obj_class', self.obj_class)
        str_repr += fmt.format('obj_subclass', self.obj_subclass)
        str_repr += fmt.format('obj_id', str(self.obj_id))
        str_repr += fmt.format('obj_num', str(self.obj_num))
        str_repr += fmt.format('obj_name', str(self.obj_name))
        
        
        if self.trk_label['obj_father'] is not None:
            father_name = self.trk_label.obj_father.trk_label.obj_name
        else:
            father_name = 'None'
            
        str_repr += fmt.format('obj_father', father_name)
        
        str_list_offsprings = []
        
        if self.trk_label['obj_offsprings']:
            for offspring_obj in self.trk_label.obj_offsprings:
               str_list_offsprings.append(offspring_obj.trk_label.obj_name)
        else: 
            str_list_offsprings.append('None')
        
        str_repr += fmt.format('obj_offsprings', str_list_offsprings[0])
        
        for str_offspring in str_list_offsprings[1:]:
            str_repr += fmt.format('', str_offspring)
    
        return str_repr
    
    def __init__(self, tgt_subclass, father = None):
        
        self.trk_label = {}
        str_allbaseclass = []
        
        for str_baseclass in self.__class__.__bases__:
            str_allbaseclass.append(str_baseclass.__name__)

        self.obj_class = ' '.join(str_allbaseclass)
        self.obj_subclass = tgt_subclass
        self.obj_id = id(self)
        
        # set obj num : init classvariable if not, assign value in label, increment class variable
        FIPLabel.free_num.setdefault(self.trk_label.obj_subclass, 0)
        self.trk_label.obj_num = FIPLabel.free_num[self.trk_label.obj_subclass]
        FIPLabel.free_num[self.trk_label.obj_subclass] += 1

        self.trk_label.obj_name = self.trk_label.obj_subclass + "_" + str(self.trk_label.obj_num)
        
        self.trk_label.obj_father = father
        
        if father is not None:
            father.trk_label.offsprings.append(self)
        
        self.trk_label.obj_offsprings = []
    
        if FIPLabel.is_debug_print: print(FIPLabel)

        
    def __str__(self):
        
        # stub as obj only contains trk_label as of now
        
        return str(self.trk_info.trk_label)
        

        