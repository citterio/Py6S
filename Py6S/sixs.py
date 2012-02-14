import subprocess
import os

from Params import *
from sixs_exceptions import *
from outputs import *

class SixS(object):
    """Wrapper for the 6S Radiative Transfer Model.
    
    This is the main class which can be used to instantiate an object which has the key methods for running 6S.
    
    The most import method in this class is the run method which writes the 6S input file,
    runs the model and processes the output.
    
    The parameters of the model are set as the attributes of this class, and the outputs are available as attributes under
    the output attribute.
    
    !!! PUT EXAMPLE HERE
    
    For a simple test to ensure that Py6S has found the correct executable for 6S simply
    run the test method of this class: SixS.Test()
    
    Attributes:
    atmos_profile         The atmospheric profile to use. Should be set to the output of an AtmosProfile method.
                          Example:
                          s.atmos_profile = AtmosProfile.PredefinedType(AtmosProfile.MidlatitudeSummer)
                      
    aero_profile          The aerosol profile to use. Should be set to the output of an AeroProfile method.
                          Example:
                          s.aero_profile = AeroProfile.PredefinedType(AeroProfile.Urban)
                      
    ground_reflectance    The ground reflectance to use. Should be set to the output of a GroundReflectance method.
                          Example:
                          s.ground_reflectance = GroundReflectance.HomogeneousLambertian(0.3)
    
    geometry              The geometrical settings, including solar and viewing angles. Should be set to an instance of a Geometry class,
                          which can then have various attributes set.
                          Example:
                          s.geometry = GeometryUser()
                          s.geometry.solar_z = 35
                          s.geometry.solar_a = 190
                          
    wavelength            The wavelength settings. Should be set to the output of the Wavelength.Wavelength() method.
                          Example:
                          s.wavelength = Wavelength.Wavelength(0.550)
                          
    atmos_corr            The settings for whether to perform atmospheric correction or not, and the parameters for this correction.
                          Should be set to the output of a AtmosCorr method.
                          Example:
                          s.atmos_corr = AtmosCorr.AtmosCorrLambertianFromReflectance(0.23)
                          
                          
    Methods:
    run -- Runs the 6S model using the parameter values set as attributes (see above), and stores the outputs in the Outputs object.
    test -- Runs a simple test of the Py6S system. This is a class method, so call as SixS.Test().
    find_path -- Finds the 6S executable. This will look in sensible locations automatically, but can also be passed a specific path to the executable.
    
    """

    # Stores the outputs from 6S as an instance of the Outputs class
    outputs = None
    
    def __init__(self, path=None):
        """Initialises the class and finds the right 6S executable to use.
        
        Sets default parameter values (a set of fairly sensible values that will allow a simple test run to be performed),
        and finds the 6S executable by searching the path.
        
        Arguments:
        path -- (Optional) The path to the 6S executable - if not specified then the system PATH and current directory are searched for the executable.
        
        """
        self.sixs_path = self.find_path(path)

        self.atmos_profile = AtmosProfile.PredefinedType(AtmosProfile.MidlatitudeSummer)
        self.aero_profile = AeroProfile.PredefinedType(AeroProfile.Maritime)
        
        self.ground_reflectance = GroundReflectance.HomogeneousLambertian(0.3)
        
        self.geometry = GeometryUser()
        self.geometry.solar_z = 32
        self.geometry.solar_z = 32
        self.geometry.solar_a = 264
        self.geometry.view_z = 23
        self.geometry.view_a = 190
        self.geometry.day = 14
        self.geometry.month = 7
        
        
        self.wavelength = Wavelength.Wavelength(0.500)
        
        self.aot550 = 0.5
        self.visibility = None
        
        self.aero_dustlike = 0
        self.aero_water = 0
        self.aero_oceanic = 0
        self.aero_soot = 0
        
        self.atmos_corr = AtmosCorr.NoAtmosCorr()
    
    def find_path(self, path=None):
      """Finds the path of the 6S executable.
      
      Arguments:
      path -- (Optional) The path to the 6S executable
      
      Finds the 6S executable on the system, either using the given path or by searching the system PATH variable and the current directory
      
      """
      if path != None:
			  return path
      else:
			  return self.which('sixs.exe') or self.which('sixs') or self.which('sixsV1.1') or self.which('sixsV1.1.exe')
        
    def which(self, program):
        def is_exe(fpath):
            return os.path.exists(fpath) and os.access(fpath, os.X_OK)

        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file

        return None

    def create_geom_lines(self):
      return str(self.geometry)

    def create_atmos_aero_lines(self):
        """Creates the atmosphere and aerosol lines for the input file"""
        return str(self.atmos_profile) + '\n' + str(self.aero_profile) + '\n'

    def create_aot_vis_lines(self):
        """Create the AOT or Visibility lines for the input file"""
        if not isinstance(self.aero_profile, AeroProfile.UserProfile):
          # We don't need to set AOT or visibility for a UserProfile, but we do for all others
          if self.aot550 != None:
            return "0\n%f value\n" % self.aot550
          elif self.visibility != None:
            return "%f\n" % self.visibility
          else:
            raise ParameterError("aot550", "You must set either the AOT at 550nm or the Visibility in km.")        
            
    def create_elevation_lines(self):
        """Create the elevation lines for the input file"""
        return """0 (target level)
0 (sensor level)\n"""

    def create_wavelength_lines(self):
        """Create the wavelength lines for the input file"""
        return self.wavelength

    def create_surface_lines(self):
        """Create the surface reflectance lines for the input file"""
        return self.ground_reflectance

    def create_atmos_corr_lines(self):
        """Create the atmospheric correction lines for the input file"""
        return self.atmos_corr

    def write_input_file(self, filename):
        """Generates a 6S input file from the parameters stored in the object
        and writes it to the given filename.
        
        The input file is guaranteed to be a valid 6S input file which can be run manually if required
        
        """
        
        with open(filename, "w") as f:
            input_file = self.create_geom_lines()
            
            input_file += self.create_atmos_aero_lines()
            
            input_file += self.create_aot_vis_lines()
            
            input_file += self.create_elevation_lines()
            
            input_file += self.create_wavelength_lines()
            
            input_file += self.create_surface_lines()
    
            input_file += self.create_atmos_corr_lines()
    
            f.write(input_file)

    def run(self):
        """Runs the 6S model and stores the outputs in the output variable.
        
        May raise an ExecutionError if the 6S executable cannot be found."""
        
        if self.sixs_path == None:
            raise ExecutionError("6S executable not found.")     
        
        self.write_input_file("tmp_in.txt")
        
        # Run the process and get the stdout from it
        process = subprocess.Popen("%s < tmp_in.txt" % self.sixs_path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        outputs = process.communicate()
        self.outputs = Outputs(outputs[0], outputs[1])

    @classmethod
    def test(self):
        """Runs a simple test to ensure that 6S and Py6S are installed correctly."""
        test = SixS()
        print "6S wrapper script by Robin Wilson"
        sixs_path = test.find_path()
        if sixs_path == None:
            print "Error: cannot find sixs executable in $PATH or current directory."
        else:
            print "Using 6S located at %s" % sixs_path
            print "Running 6S using a set of test parameters"
            test.run()
            print "The results are:"
            print "Expected result: %f" % 619.158
            print "Actual result: %f" % test.outputs.diffuse_solar_irradiance
            if (test.outputs.diffuse_solar_irradiance - 619.158 < 0.01):
                print "#### Results agree, Py6S is working correctly"