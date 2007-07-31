"""Least squares smooting and interpolation.

   measure the speed of least squares.

   ________________________
   General comments
   
   The max_points_per_cell does effect the time spent solving a
   problem.  The best value to use is probably dependent on the number
   of triangles.  Maybe develop a simple imperical algorithm, based on
   test results.
   
   Duncan Gray
   Geoscience Australia, 2004.
"""


import os
import sys
import time
from random import seed, random
import tempfile
import profile , pstats
import tempfile

from anuga.fit_interpolate.interpolate import Interpolate
from anuga.fit_interpolate.fit import Fit
from anuga.pmesh.mesh import Mesh
from anuga.geospatial_data.geospatial_data import Geospatial_data

def mem_usage():
    '''
    returns the rss.

  RSS  The total amount of physical memory used by  the  task,  in  kilo-
            bytes,  is  shown  here.  For ELF processes used library pages are
            counted here, for a.out processes not.
            
    Only works on nix systems.
    '''
    import string
    p=os.popen('ps uwp %s'%os.getpid()) 
    lines=p.readlines()
    #print "lines", lines
    status=p.close() 
    if status or len(lines)!=2 or sys.platform == 'win32': 
        return None 
    return int(string.split(lines[1])[4]) 




class BenchmarkLeastSquares:

    """

    Note(DSG-DSG): If you are interested in benchmarking fitting, before
    and after blocking O:\1\dgray\before_blocking_subsandpit is before blocking

    """

    def __init__(self):
        pass

    def trial(self,
              num_of_points=20000,
              maxArea=1000,
              max_points_per_cell=4,
              is_fit=True,
              use_least_squares=False,
              use_file_type=None,
              blocking_len=500000,
              segments_in_mesh=True,
              save=False,
              verbose=False,
              run_profile=False):
        '''
        num_of_points 
        '''
        #print "num_of_points",num_of_points
        #print "maxArea",maxArea
        #print "max_points_per_cell", max_points_per_cell

        mesh_dict = self._build_regular_mesh_dict(maxArea=maxArea,
                                                  is_segments=segments_in_mesh,
                                                  save=save)
        points_dict = self._build_points_dict(num_of_points=num_of_points)
            
        #Initial time and memory
        t0 = time.time()
        #m0 = None on windows
        m0 = mem_usage()
        
        profile_file = "P" + str(num_of_points) + \
                       "T" + str(len(mesh_dict['triangles'])) + \
                       "PPC" + str(max_points_per_cell) + \
                       ".txt"
                       
        if use_least_squares is True:
            from anuga.where.least_squares import Interpolation
            interp = Interpolation(mesh_dict['vertices'],
                                   mesh_dict['triangles'],
                                   points_dict['points'],
                                   expand_search=True,
                                   verbose = False,
                                   max_points_per_cell = max_points_per_cell) 
            if is_fit is True:
                print "Fit in least squares"
                calc = interp.fit_points(points_dict['point_attributes'])
                
            else:
                # run an interploate problem.
                print "Interpolate!"
                calc = interp.interpolate(mesh_dict['vertex_attributes'])
        else: 
            if is_fit is True:
                from anuga.fit_interpolate.fit import Fit
                interp = Fit(mesh_dict['vertices'],
                                 mesh_dict['triangles'], 
                                 max_vertices_per_cell = max_points_per_cell)
                print "Fit in Fit"
                if use_file_type == None:
                    calc = interp.fit(points_dict['points'],
                                      points_dict['point_attributes'])
                else:
                    #check that the type
                    fileName = tempfile.mktemp("." + use_file_type)
                    G1 = Geospatial_data(points_dict['points'],
                                         points_dict['point_attributes'])
                    G1.export_points_file(fileName, absolute=True)

                    if run_profile:
                    
                        s = """interp.fit(fileName, verbose=verbose)"""
                        pobject = profile.Profile()
                        presult = pobject.runctx(s,
                                                 vars(sys.modules[__name__]),
                                                 vars())
                        prof_file = tempfile.mktemp(".prof")
                        presult.dump_stats(prof_file)
                        #
                        # Let process these results
                        S = pstats.Stats(prof_file)
                        saveout = sys.stdout 
                        pfile = open(profile_file, "w")
                        sys.stdout = pfile
                        s = S.sort_stats('cumulative').print_stats(30)
                        sys.stdout = saveout 
                        pfile.close()
                        os.remove(prof_file)
                    else:
                        interp.fit(fileName, verbose=verbose)
                    os.remove(fileName)
                    
            else:
                # run an interploate problem.
                print "Interpolate!"
                
                interp = Interpolate(mesh_dict['vertices'],
                                     mesh_dict['triangles'], 
                                 max_vertices_per_cell = max_points_per_cell)
                s = """calc = interp.interpolate(mesh_dict['vertex_attributes']
                                          ,points_dict['points']
                                          ,start_blocking_len=blocking_len)"""
                
                fileName = tempfile.mktemp(".prof")
                profile.run(s, fileName) #profile_file)
                
                S = pstats.Stats(fileName)
                s = S.sort_stats('cumulative').print_stats(30)
                print "***********"
                print s
                print "***********"
                pfile = file.open(profile_file, "w")
                pfile.write(s)
                pfile.close()
        time_taken_sec = (time.time()-t0)
        m1 = mem_usage()
        if m0 is None or m1 is None:
            memory_used = None
        else:
            memory_used = (m1 - m0)
        #print 'That took %.2f seconds' %time_taken_sec
        return time_taken_sec, memory_used, len(mesh_dict['triangles'])

    def _build_regular_mesh_dict(self,
                                 maxArea=1000,
                                 is_segments=True,
                                 save=False):
      # make a normalised mesh
        # pretty regular size, with some segments thrown in. 
        m = Mesh()
        m.addUserVertex(0,0)
        m.addUserVertex(1.0,0)
        m.addUserVertex(0,1.0)
        m.addUserVertex(1.0,1.0)
        
        m.auto_segment(alpha = 100 )

        if is_segments:
            dict = {}
            dict['points'] = [[.10,.10],[.90,.20]]
            dict['segments'] = [[0,1]] 
            dict['segment_tags'] = ['wall1']   
            m.addVertsSegs(dict)
    
            dict = {}
            dict['points'] = [[.10,.90],[.40,.20]]
            dict['segments'] = [[0,1]] 
            dict['segment_tags'] = ['wall2']   
            m.addVertsSegs(dict)
        
            dict = {}
            dict['points'] = [[.20,.90],[.60,.60]]
            dict['segments'] = [[0,1]] 
            dict['segment_tags'] = ['wall3'] 
            m.addVertsSegs(dict)
        
            dict = {}
            dict['points'] = [[.60,.20],[.90,.90]]
            dict['segments'] = [[0,1]] 
            dict['segment_tags'] = ['wall4']   
            m.addVertsSegs(dict)

        m.generateMesh(mode = "Q", maxArea = maxArea, minAngle=20.0)       
        if save is True:
            m.export_mesh_file("aaaa.tsh")
        mesh_dict =  m.Mesh2IOTriangulationDict()

        #Add vert attribute info to the mesh
        mesh_dict['vertex_attributes'] = []
        # There has to be a better way of doing this..
        for vertex in mesh_dict['vertices']:
            mesh_dict['vertex_attributes'].append([10.0])

        return mesh_dict

    def _build_points_dict(self, num_of_points=20000):
        
        points_dict = {}
        points = []
        point_atts = []

        for point in range(num_of_points):
            points.append([random(), random()])
            point_atts.append(10.0)

        points_dict['points'] = points
        points_dict['point_attributes'] = point_atts
        return points_dict


#-------------------------------------------------------------
if __name__ == "__main__":
        b = BenchmarkLeastSquares()
        b._build_regular_mesh_dict()
        b._build_points_dict()
