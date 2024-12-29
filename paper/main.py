import aerosandbox as asb
import numpy as np
from pathlib import Path
from rich import print
import subprocess
import platform

def genSample():
    from smt.sampling_methods.lhs import LHS
    from _cad import DesVars

    desvars=DesVars()

    bds=desvars.bounds
    print(f"dim is {bds.shape[0]}")
    
    sampler=LHS(xlimits=bds, random_state=1)
    x=sampler(1500)
    
    baseline=desvars.baseline
    x=np.vstack([baseline,x[:-1]])

    np.savetxt('./sample.csv',x,delimiter=',',fmt='%.6f')

# def callNX():
#     af=asb.KulfanAirfoil('naca0012').set_TE_thickness(0.0025)
#     coords=af.coordinates*1000
#     coords_str=""
#     for i in coords:
#         tmp=','.join([f"{j:.6f}" for j in i])
#         tmp="["+tmp+",0.0],"
#         coords_str+=tmp
#     coords_str='['+coords_str+']'

#     nxfile=Path("./nx.py").read_text()
#     nxfile=nxfile.replace(r"af_coords = [[0, 0, 0], [0, 0, 0]]",f"af_coords = {coords_str}")

#     Path("./nx_test.py").write_text(nxfile)

def callNX():
    from mpi4py import MPI

    def _call(desvars,outfiles,pid):
        baseaf:asb.KulfanAirfoil=asb.load("./data/baseline.asb",verbose=False)

        nx_template_old = Path("./nx.py").read_text()
        nxfile=Path("./model.prt").absolute().as_posix()
        nx_template_old = nx_template_old.replace(r'templatefile = "xxx"', f'templatefile = "{nxfile}"')

        for i in range(desvars.shape[0]):
            slatfile = (Path("./result/CAD") / f"{outfiles[i]:03d}_slat.x_t").absolute().as_posix()
            mainfile = (Path("./result/CAD") / f"{outfiles[i]:03d}_main.x_t").absolute().as_posix()
            flapfile = (Path("./result/CAD") / f"{outfiles[i]:03d}_flap.x_t").absolute().as_posix()

            kulfan=desvars[i,:9]
            af=baseaf.deepcopy()
            af.lower_weights+=kulfan[:4]
            af.upper_weights+=kulfan[4:8]
            af.leading_edge_weight+=kulfan[8]
            af=af.set_TE_thickness(1.5e-3)
            af_coords=af.coordinates*1000
            coords_str=""
            for icoords in af_coords:
                tmp=','.join([f"{j:.6f}" for j in icoords])
                tmp="["+tmp+",0.0],"
                coords_str+=tmp
            coords_str='['+coords_str+']'
            
            slat_flap=','.join([f"{_:.6f}" for _ in desvars[i,9:]])

            nx_template_new = nx_template_old
            nx_template_new = nx_template_new.replace('slatfile = "xxx"', f'slatfile = "{slatfile}"')
            nx_template_new = nx_template_new.replace('mainfile = "xxx"', f'mainfile = "{mainfile}"')
            nx_template_new = nx_template_new.replace('flapfile = "xxx"', f'flapfile = "{flapfile}"')
            nx_template_new = nx_template_new.replace("desvars = [50.0, 90.0, 0.9, 50.0]", f"desvars = [{slat_flap}]")
            nx_template_new = nx_template_new.replace(r"af_coords = [[0, 0, 0], [0, 0, 0]]",f"af_coords = {coords_str}")
            nx_template_new = nx_template_new.replace("tag = 0", f"tag = {outfiles[i]}")

            nx_script = f"./runtime/nx_rank_{pid:03d}.py"
            with open(nx_script, "w") as fout:
                fout.write(nx_template_new)

            nx_cmd = ["D:/Siemens/NX2312/NXBIN/run_journal.exe", nx_script]
            p = subprocess.run(nx_cmd)

    
    comm=MPI.COMM_WORLD
    mpiSize=comm.Get_size()
    mpiRank=comm.Get_rank()

    if mpiRank==0:
        # dvs=np.loadtxt("./sample.csv",delimiter=',',ndmin=2)[[0,1,2],:]
        dvs=np.loadtxt("./sample.csv",delimiter=',',ndmin=2)
        outfiles=np.arange(dvs.shape[0])

        chunks_all_desvars=np.array_split(dvs,mpiSize,axis=0)
        chunks_outfiles=np.array_split(outfiles,mpiSize,axis=0)
    else:
        chunks_all_desvars=None
        chunks_outfiles=None
    indiv_all_desvars=comm.scatter(chunks_all_desvars,root=0)
    indiv_all_outfiles=comm.scatter(chunks_outfiles,root=0)
    _call(desvars=indiv_all_desvars,outfiles=indiv_all_outfiles,pid=mpiRank)

def runCFD(rank,port,cad):
    for i in cad:
        cfdScript = Path("./run_star.java").read_text()

        flap_file = (Path("./result/CAD") / f"{i:03d}_flap.x_t").absolute().as_posix()
        main_file = (Path("./result/CAD") / f"{i:03d}_main.x_t").absolute().as_posix()
        slat_file = (Path("./result/CAD") / f"{i:03d}_slat.x_t").absolute().as_posix()
        outfile = (Path("./result/CFD") / f"{i:03d}.csv").absolute().as_posix()

        cfdScript = cfdScript.replace("run_star", f"rank_{rank}")
        cfdScript = cfdScript.replace(
            r"D:\\paper\\Thesis\\thesis\\resource\\L1T2\\result\\NX\\CAD\\000_flap.x_t", flap_file
        )
        cfdScript = cfdScript.replace(
            r"D:\\paper\\Thesis\\thesis\\resource\\L1T2\\result\\NX\\CAD\\000_main.x_t", main_file
        )
        cfdScript = cfdScript.replace(
            r"D:\\paper\\Thesis\\thesis\\resource\\L1T2\\result\\NX\\CAD\\000_slat.x_t", slat_file
        )
        cfdScript = cfdScript.replace(r"C:\\Users\\Zcaic\\Desktop\\L1T2\\result\\test.csv", outfile)

        javafile = (Path("./runtime") / f"rank_{rank}.java").absolute()
        javafile.write_text(cfdScript)

        host = platform.uname()[1] + ":" + str(port)
        cmd = ["starccm+", "-host", host, "-batch", javafile.as_posix()]
        p = subprocess.run(cmd, stdout=subprocess.DEVNULL)


def post_callNX():
    from mpi4py import MPI

    def _call(desvars,outfiles,pid):
        baseaf:asb.KulfanAirfoil=asb.load("./data/baseline.asb",verbose=False)

        nx_template_old = Path("./nx_post.py").read_text()
        nxfile=Path("./model.prt").absolute().as_posix()
        nx_template_old = nx_template_old.replace(r'templatefile = "xxx"', f'templatefile = "{nxfile}"')

        for i in range(desvars.shape[0]):
            slatfile = (Path("./result/OPTIMAL") / f"{outfiles[i]:03d}_slat.x_t").absolute().as_posix()
            mainfile = (Path("./result/OPTIMAL") / f"{outfiles[i]:03d}_main.x_t").absolute().as_posix()
            flapfile = (Path("./result/OPTIMAL") / f"{outfiles[i]:03d}_flap.x_t").absolute().as_posix()

            kulfan=desvars[i,:9]
            af=baseaf.deepcopy()
            af.lower_weights+=kulfan[:4]
            af.upper_weights+=kulfan[4:8]
            af.leading_edge_weight+=kulfan[8]
            af=af.set_TE_thickness(1.5e-3)
            af_coords=af.coordinates*1000
            coords_str=""
            for icoords in af_coords:
                tmp=','.join([f"{j:.6f}" for j in icoords])
                tmp="["+tmp+",0.0],"
                coords_str+=tmp
            coords_str='['+coords_str+']'
            
            slat_flap=','.join([f"{_:.6f}" for _ in desvars[i,9:]])

            nx_template_new = nx_template_old
            nx_template_new = nx_template_new.replace('slatfile = "xxx"', f'slatfile = "{slatfile}"')
            nx_template_new = nx_template_new.replace('mainfile = "xxx"', f'mainfile = "{mainfile}"')
            nx_template_new = nx_template_new.replace('flapfile = "xxx"', f'flapfile = "{flapfile}"')
            nx_template_new = nx_template_new.replace("desvars = [50.0, 90.0, 0.9, 50.0]", f"desvars = [{slat_flap}]")
            nx_template_new = nx_template_new.replace(r"af_coords = [[0, 0, 0], [0, 0, 0]]",f"af_coords = {coords_str}")
            nx_template_new = nx_template_new.replace("tag = 0", f"tag = {outfiles[i]}")

            nx_script = f"./runtime/nx_rank_{pid:03d}.py"
            with open(nx_script, "w") as fout:
                fout.write(nx_template_new)

            nx_cmd = ["D:/Siemens/NX2312/NXBIN/run_journal.exe", nx_script]
            p = subprocess.run(nx_cmd)

    
    comm=MPI.COMM_WORLD
    mpiSize=comm.Get_size()
    mpiRank=comm.Get_rank()

    if mpiRank==0:
        # dvs=np.loadtxt("./sample.csv",delimiter=',',ndmin=2)[[0,1,2],:]
        dvs=np.loadtxt("./result/OPTIMAL/pfx.csv",delimiter=',',ndmin=2)
        outfiles=np.arange(dvs.shape[0])

        chunks_all_desvars=np.array_split(dvs,mpiSize,axis=0)
        chunks_outfiles=np.array_split(outfiles,mpiSize,axis=0)
    else:
        chunks_all_desvars=None
        chunks_outfiles=None
    indiv_all_desvars=comm.scatter(chunks_all_desvars,root=0)
    indiv_all_outfiles=comm.scatter(chunks_outfiles,root=0)
    _call(desvars=indiv_all_desvars,outfiles=indiv_all_outfiles,pid=mpiRank)




if __name__=="__main__":
    # genSample()
    # callNX()
    # runCFD(0,47827,np.arange(369,380))
    # runCFD(1,47828,np.arange(380,390))
    # runCFD(2,47829,np.arange(390,400))
    post_callNX()