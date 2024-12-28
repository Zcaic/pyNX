import aerosandbox as asb

af = asb.KulfanAirfoil("rae2822").set_TE_thickness(2.4e-3)
af.write_dat("./af.dat", include_name=False)
