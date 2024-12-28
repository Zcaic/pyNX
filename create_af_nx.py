# import aerosandbox as asb
# import numpy as np

# af = asb.KulfanAirfoil("n63415").set_TE_thickness(2.4e-3)
# coords = np.hstack([af.coordinates*1000.0,np.zeros_like(af.coordinates[:,[0]])])
# np.savetxt("./n63415.dat",coords)

import NXOpen

af_file = "C:/Users/Zcaic/Desktop/test/n63415.dat"
scale = 1000.0

theSession  = NXOpen.Session.GetSession() #type: NXOpen.Session
part = theSession.Parts.Work
splineEx = part.Features.CreateStudioSplineBuilderEx(NXOpen.NXObject.Null)

with open(af_file,"r") as fin:
    for line in fin:
        line = line.strip()
        if line:
            coords = line.split()
            coords = NXOpen.Point3d(float(coords[0])*scale,float(coords[1])*scale,0.0)
            pt = part.Points.CreatePoint(coords)
            geoCons = splineEx.ConstraintManager.CreateGeometricConstraintData()
            geoCons.Point = pt
            splineEx.ConstraintManager.Append(geoCons)

splineEx.Commit()
splineEx.Destroy()




