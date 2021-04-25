#!/usr/bin/env python
import os
import sys
import csv
import osgeo.osr as osr
import osgeo.ogr as ogr
import re
import datetime
from  ftplib import FTP
from subprocess import call
from subprocess import Popen
import glob

#https://ladsweb.nascom.nasa.gov/archive/geoMeta/5/AQUA/2011/MYD03_2011-01-01.txt 
data_pass = sys.argv[1] #"20160301"
sat = sys.argv[2] #"aqua"
ano = data_pass[:-4] #"2016"
mes = data_pass[4:-2] #03
dia = data_pass[6:] #01
yyyy_mm= "%s_%s" % (ano, mes)
path_to_download = "/dados/L1_%s/%s/hdf/%s_MODIS_%s%s%s/" % (sat, yyyy_mm,
                                                             sat, ano, mes, dia)
if not os.path.exists(path_to_download):
        os.makedirs(path_to_download)

if sat.upper() == "AQUA":
	prod= "MYD"
if sat.upper() == "TERRA":
	prod= "MOD"

lnk = "https://ladsweb.nascom.nasa.gov/archive/"
g = "geoMeta/5/%s/%s/"%(sat.upper(), ano)
file2down = "%s03_%s-%s-%s.txt"%(prod,ano,mes,dia)
print "arquivo para download.: %s"%(file2down)

cmd = "wget -nv -c %s -O %s" % (lnk + g + file2down, path_to_download + file2down) 
proc = Popen(cmd.split(" "))
proc.wait()


# MODIS Aqua GEOGRAPHIC METADATA TEXT FILE day 2011-01-01

pathtofile= "%s%s"%(path_to_download,file2down)
print "processing: %s"%(pathtofile)

ftext= open(pathtofile,"rb")
l0=ftext.readline()
da = re.search("\d{4}",l0)
d_ano= da.group(0)
data= l0[da.start(0):da.start(0)+10]
date = datetime.datetime.strptime(data,"%Y-%m-%d").date()
dateinit = datetime.datetime.strptime("%s%s%s" %(d_ano,1,1),"%Y%m%d").date()
julian = datetime.date.toordinal(date) - datetime.date.toordinal(dateinit) + 1
print " dia juliano %.3d" % (julian)

imlist=[]

x= [l.split(",") for l in ftext if "#" not in l]
print x
for xx in x:
        if len(xx) < 8:
           print "String Rejected: " + xx
           continue

	EBC= float(xx[5])
	NBC= float(xx[6])
	SBC= float(xx[7])
	WBC= float(xx[8])
        file_to_down=str(xx[0])
        h = int(file_to_down.split(".")[2][:1])
        if h > 0:
           wkt = "POLYGON ((%.6f %.6f,%.6f %.6f,%.6f %.6f,%.6f %.6f,%.6f %.6f))"%(EBC,NBC,WBC,NBC,WBC,SBC,EBC,SBC,EBC,NBC)
           bb = "POLYGON((-25 20, -95 20, -95 -60, -25 -60, -25 20))"
           poly_scene = ogr.CreateGeometryFromWkt(wkt)
           poly_bb = ogr.CreateGeometryFromWkt(bb)
           if poly_bb.Contains(poly_scene):
                dttime = xx[1].split(" ")
                dt = dttime[0].split("-")
                tm = dttime[1].split(":")
                # Search for W files
                pattw = "/L3_%s/%s_%s/queimada/indice/%s_MODIS_%s_%s*/*W" \
                        % (sat, ano, mes, sat, data_pass, tm[0])
                if len(glob.glob(pattw)) > 0:
                     print "File discarted because the W file exists: " \
                           + file_to_down
                     continue

                imlist.append(file_to_down)
           else:
                print "File discarted: " + str(file_to_down)
        else:
            print "File rejected: " + str(file_to_down)

print "############################################################ DONE PROC"	

a= "allData/5/%s03/%s/%.3d/" %(prod,d_ano,julian)
b= "allData/5/%s021KM/%s/%.3d/" %(prod,d_ano,julian)

# csv file download from 21km directory
cmd = "wget -nv -nc -c %s.csv -O %s" % (lnk + b, path_to_download + ".csv")
print cmd
proc = Popen(cmd.split(" "))
proc.wait()


#lnk="https://ladsweb.nascom.nasa.gov/archive/"
for f03 in imlist:
    cmd = "wget -nv -nc -c %s -O %s" % (lnk + a + f03, path_to_download + f03)
    print cmd
    proc = Popen(cmd.split(" "))
    proc.wait()

    f21 = f03.replace("%s03"%(prod),"%s021KM"%(prod))[:-17]
    # wget -r -nv -nd -c --accept-regex="MYD021KM.A2016032.1720.006.*hdf" https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/5/MYD021KM/2016/032/ -P /tmp
    # nc - no overwriting
    # nd - no create directories
    # nv - no verbose
    #cmd = "wget -r -nc -nd -nv -c --accept-regex=%s %s -P %s" % (f21, lnk + b, path_to_download)
    #cmd = "wget -r -nc -nd -c --accept-regex=%s %s -P %s" % (f21, lnk + b, path_to_download)
    #cmd = "wget -nv -nc -c %s/.csv -O %s" % (lnk + a + f21, path_to_download)
    #print cmd
    #proc = Popen(cmd.split(" "))
    #proc.wait()

    fcsv = csv.reader(open(path_to_download + ".csv", 'r'))
    print f21, path_to_download + ".csv"
    for r in fcsv:
        if f21 in r[0]:
           cmd = "wget -nv -nc -c %s -O %s" % (lnk + b + r[0], path_to_download + r[0])
           print cmd
           proc = Popen(cmd.split(" "))
           proc.wait()
           break


print "Fim do download"

arr_hdf = "/home/queimadas/victorino/gera_indice_w/recuperacao_acervo/arruma_hdf_tiles.sh"
data_pass = "%s%s%s" % (ano, mes, dia)
cmd = [arr_hdf, data_pass, sat]
print "%s %s %s" % (cmd[0], cmd[1], cmd[2])
#call(cmd)
proc = Popen(cmd)
proc.wait()
