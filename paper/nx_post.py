import math
import NXOpen
import NXOpen.Features
import NXOpen.GeometricUtilities
import NXOpen.UF

templatefile = "xxx"
slatfile = "xxx"
mainfile = "xxx"
flapfile = "xxx"
desvars = [50.0, 90.0, 0.9, 50.0]
af_coords = [[0, 0, 0], [0, 0, 0]]
tag = 0


def main():
    theSession = NXOpen.Session.GetSession()  # type: NXOpen.Session
    basepart, status = theSession.Parts.OpenActiveDisplay(
        templatefile, NXOpen.DisplayPartOption.AllowAdditional
    )
    theUFSession = NXOpen.UF.UFSession.GetUFSession()
    workPart = theSession.Parts.Work
    displayPart = theSession.Parts.Display

    markId1 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "af")

    studioSpline1 = workPart.Features.FindObject("SPLINE(2)")
    studioSpline1.MakeCurrentFeature()

    studioSplineBuilderEx1 = workPart.Features.CreateStudioSplineBuilderEx(studioSpline1)
    for _ in range(1):
        for i in range(399):
            geometricConstraintData = studioSplineBuilderEx1.ConstraintManager.FindItem(i)
            pt = geometricConstraintData.Point
            coord = NXOpen.Point3d(*af_coords[i])
            pt.SetCoordinates(coord)
            studioSplineBuilderEx1.Evaluate()
        nXObject1 = studioSplineBuilderEx1.Commit()
        studioSplineBuilderEx1.Destroy()

        try:
            nerrs = theSession.UpdateManager.DoUpdate(markId1)
            UpdateForExternalChange(theUFSession, workPart)
        except:
            print(f"{tag} is error!", flush=True)

    # ------------------------------------------------------------------------------------------------------------------
    markId1 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "local")
    parameterization(workPart, theSession, markId1, "slat_B", desvars[9], update=False)
    parameterization(workPart, theSession, markId1, "slat_Cx", desvars[10], update=False)
    parameterization(workPart, theSession, markId1, "slat_Cy", desvars[11], update=False)
    parameterization(workPart, theSession, markId1, "slat_D", desvars[12], update=False)

    parameterization(workPart, theSession, markId1, "flap_B", desvars[0], update=False)
    parameterization(workPart, theSession, markId1, "flap_Cx", desvars[1], update=False)
    parameterization(workPart, theSession, markId1, "flap_Cy", desvars[2], update=False)
    parameterization(workPart, theSession, markId1, "flap_Dx", desvars[3], update=False)
    parameterization(workPart, theSession, markId1, "flap_Dy", desvars[4], update=False)
    parameterization(workPart, theSession, markId1, "flap_E", desvars[5], update=False)

    try:
        f = workPart.Features.FindObject("SKETCH(4)")
        f.MakeCurrentFeature()
        nerrs = theSession.UpdateManager.DoUpdate(markId1)
        UpdateForExternalChange(theUFSession, workPart)
    except:
        print(f"{tag} is error!", flush=True)

    # -----------------------------------------------------------------------------------------------------------------------
    markId1 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "global")
    parameterization(workPart, theSession, markId1, "slat_theta", desvars[15], update=False)
    parameterization(workPart, theSession, markId1, "slat_gap", desvars[13], update=False)
    parameterization(workPart, theSession, markId1, "slat_overlap", desvars[14], update=False)
    parameterization(workPart, theSession, markId1, "flap_theta", desvars[8], update=False)
    parameterization(workPart, theSession, markId1, "flap_gap", desvars[6], update=False)
    parameterization(workPart, theSession, markId1, "flap_overlap", desvars[7], update=False)

    try:
        f = workPart.Features.FindObject("SKETCH(6)")
        f.MakeCurrentFeature()
        nerrs = theSession.UpdateManager.DoUpdate(markId1)
        UpdateForExternalChange(theUFSession, workPart)
    except:
        print(f"{tag} is error!", flush=True)

    # -------------------------------------------------------------------------------------------------------------------------
    markId1 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "gen_te")

    try:
        f = workPart.Features.FindObject("SKETCH(7)")
        f.MakeCurrentFeature()
        nerrs = theSession.UpdateManager.DoUpdate(markId1)
        UpdateForExternalChange(theUFSession, workPart)
    except:
        print(f"{tag} is error!", flush=True)


    # -------------------------------------------------------------------------------------------------------------------------
    markId1 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "gen_cad")

    try:
        f = workPart.Features.FindObject("EXTRUDE(8)")
        f.MakeCurrentFeature()
        nerrs = theSession.UpdateManager.DoUpdate(markId1)
        UpdateForExternalChange(theUFSession, workPart)
    except:
        print(f"{tag} is error!", flush=True)

    # ---------------------------------------------------------------------------------------------------------------------------
    workPart.SaveAs(f"result/OPTIMAL/model_{tag:03d}.prt")
    export(workPart, theSession)


def parameterization(
    part: NXOpen.Part, session: NXOpen.Session, markId, name: str, value: float, update=True
):
    expre = part.Expressions.FindObject(name)
    part.Expressions.Edit(expre, f"{value:.6f}")
    if update:
        errs = session.UpdateManager.DoUpdate(markId)
        if errs != 0:
            print(f"{tag} is error!", flush=True)
    else:
        return 0


def UpdateForExternalChange(theUFSession, workPart: NXOpen.Part):
    ruleName = theUFSession.Cfi.GetUniqueFilename()
    workPart.RuleManager.CreateDynamicRule(
        "root:", ruleName, "Any", "%ug_updateForExternalChange(false)", ""
    )
    workPart.RuleManager.Evaluate(ruleName + ":")
    workPart.RuleManager.DeleteDynamicRule("root:", ruleName)


def export(part: NXOpen.Part, session: NXOpen.Session):
    slat_part = part.Bodies.FindObject("EXTRUDE(8)1")
    main_part = part.Bodies.FindObject("EXTRUDE(8)2")
    flap_part = part.Bodies.FindObject("EXTRUDE(8)3")

    exporter = session.DexManager.CreateParasolidExporter()
    exporter.ObjectTypes.Curves = True
    exporter.ObjectTypes.Surfaces = True
    exporter.ObjectTypes.Solids = True
    exporter.ParasolidVersion = NXOpen.ParasolidExporter.ParasolidVersionOption.Current
    exporter.InputFile = templatefile
    exporter.ExportSelectionBlock.SelectionScope = NXOpen.ObjectSelector.Scope.SelectedObjects

    added = exporter.ExportSelectionBlock.SelectionComp.Add(slat_part)
    exporter.OutputFile = slatfile
    exporter.Commit()

    exporter.ExportSelectionBlock.SelectionComp.Clear()
    added = exporter.ExportSelectionBlock.SelectionComp.Add(main_part)
    exporter.OutputFile = mainfile
    exporter.Commit()

    exporter.ExportSelectionBlock.SelectionComp.Clear()
    added = exporter.ExportSelectionBlock.SelectionComp.Add(flap_part)
    exporter.OutputFile = flapfile
    exporter.Commit()

    exporter.Destroy()


if __name__ == "__main__":
    main()
