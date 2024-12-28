import NXOpen


def main():
    af_file = "C:/Users/Zcaic/Desktop/test/af.dat"
    scale = 1000.0

    session = NXOpen.Session.GetSession()
    part = session.Parts.Work

    spline = part.Features.FindObject("SPLINE(1)")
    splinebuilder = part.Features.CreateStudioSplineBuilderEx(spline)

    with open(af_file, "r") as fin:
        index = 0
        for line in fin:
            line = line.strip()
            if line:
                line = line.split()
                geoCons = splinebuilder.ConstraintManager.FindItem(index)
                pt = geoCons.Point
                pt.SetCoordinates(NXOpen.Point3d(float(line[0]) * scale, float(line[1]) * scale, 0.0))
                index += 1
    splinebuilder.Evaluate()
    splinebuilder.Commit()
    splinebuilder.Destroy()

    markID = session.SetUndoMark(session.MarkVisibility.Visible, "Update model")
    session.UpdateManager.UpdateModel(part, markID)

if __name__ == "__main__":
    main()
