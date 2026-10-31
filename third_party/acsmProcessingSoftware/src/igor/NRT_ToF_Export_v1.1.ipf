#pragma TextEncoding = "UTF-8"
#pragma rtGlobals=3        // Use modern global access method and strict wave access.
#pragma version=1.1

#include "twV2_3_18_daq2_instr4_ACSM" version>=40, optional

/////////////////////////////////////////////////////////////
//
// Description :
// -------------
//    Generate raw text files from ACSM acquisition software
//
// Copyright (©) 2022:
// -------------------
//     Université Aix-Marseille I (AMU)
//     Commissariat à l'énergie atomique et aux énergies alternatives (CEA) ;
//     Centre national de la recherche scientifique (CNRS);
// 
// Author(s) :
// --------
//     AMU Benjamin Chazeau, benjamin-dot-chazeau-at-univ-hyphen-amu-dot-fr
//     CEA/LSCE Jean-Eudes Petit, jean-hyphen-eudes-dot-petit-at-lsce-dot-ipsl-dot-fr
//
// License :
// -------------
//    This program is free software: you can redistribute it and/or modify
//    it under the terms of the GNU Affero General Public License as published
//    by the Free Software Foundation, either version 3 of the License, or
//    (at your option) any later version.
//
//    This program is distributed in the hope that it will be useful,
//    but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//    GNU Affero General Public License for more details.
//
//    You should have received a copy of the GNU Affero General Public License
//    along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
//
// History :
// ---------
//   v1.1.0 : 2022/10/27
//     - first official release
//     - compatible only with twV2_3_18_daq2_instr4_ACSM.ipf v40
//
//
/////////////////////////////////////////////////////////////

StrConstant export_version="1.1"


//Autolycos is a procedure which is set as a background task for ToF-ACSM OA matrix export 

//OrgMx_PathName is the disk path where OA spectra will be stored
//TimeRes must be in seconds and not below the ACSM time resolution 


Menu "Autolycos"
    "Initialize Tool", PrepTool() 
    "Tool Window", Dowindow/F Autolycos_Panel
End    
    
Function Autolycos_Panel()
    PauseUpdate; Silent 1        // building window...
    NewPanel/W=(200,10,605,300)/K=1
    ModifyPanel fixedSize=1
    SetDrawLayer UserBack
    SetDrawEnv fname= "Sylfaen",fstyle= 1,textrgb= (32768,32770,65535)
    DrawText 40,45,"\\Z32\\F'Sylfaen'AUTOLYCOS  v."+export_version
    SetDrawEnv linefgc= (34952,34952,34952),fillpat= 50,fillfgc= (56797,56797,56797),fillbgc= (52428,52428,52428)
    DrawRect 8,49,396,225
    PopupMenu PM_Station, fSize=14, pos={6,55}, size={100,20}, value = "select;"+InputLists("Station"), title="\f01Station Name", proc = StationInput_proc, disable = 0,fstyle=1,font="Arial"
    //wave/T ToF_QuadW=root:Autolycos:ToF_QuadW
    string ToF_str="UMR ToF"
    SetVariable PM_Spectro, fSize=14, pos={200,55}, size={180,20}, value=ToF_str, title="\f01Spectrometer", disable = 0,fstyle=0,font="Arial",noedit=1
    
    SVAR/Z SN_str=root:Autolycos:SN_str
    SetVariable Set_SN, fSize=10, pos={230,80}, size={150,20}, value = SN_str, title="\f02Serial Number",fstyle=2,font="Arial",noedit=0
    PopupMenu PM_Lens, fSize=14, pos={6,120}, size={100,20}, value = "select;"+InputLists("Lens"), title="\f01Lens", proc = LensInput_proc, disable = 0,fstyle=1,font="Arial"
    PopupMenu PM_Vap, fSize=14, pos={200,120}, size={100,20}, value = "select;"+InputLists("Vaporizer"), title="\f01Vaporizer", proc = VapInput_proc, disable = 0,fstyle=1,font="Arial"
    
    NVAR/Z GeneratePMFInput=root:Autolycos:GeneratePMFInput
    CheckBox PMFBox, fSize=14, pos={20,155},title="Generate PMF Input ?", variable=GeneratePMFInput, font="Arial"
	
	NVAR/Z GenerateSoFi=root:Autolycos:GenerateSoFi
	CheckBox SoFiBox, fSize=14, pos={250,155},title="SoFi RT", variable=GenerateSoFi, font="Arial"

	SVAR/Z NextCloud_path=root:Autolycos:NextCloud_path
	SetVariable Set_ExportPath,title="Save Data Folder",pos={7,190},size={323,19},value=NextCloud_path,fSize=12,noedit=1,font="Arial", disable=0
	Button Set_PathToR_button,title="\\f01SET",pos={336,190},size={50,20},fSize=14,fColor=(39168,39168,39168),font="Arial", proc=SetPath_proc, disable=0
	
	NVAR/Z StartStop_bool=root:Autolycos:StartStop_bool
	if (StartStop_bool==0)
		Button RunButton,title="START",pos={24,230},size={355,40},fSize=20,fstyle=1,fColor=(26112,52224,0),proc=LaunchExport,font="Arial",disable=0
	elseif (StartStop_bool==1)
		Button RunButton,title="STOP",pos={24,230},size={355,40},fSize=20,fstyle=1,fColor=(65280,16384,16384),proc=LaunchExport,font="Arial",disable=0
	endif
    
//    Button Autolycos_Start,pos={81.60,160.80},size={69.60,30.60},proc=Button_StartTask,title="Start"
//    Button Autolycos_Start,font="Sylfaen",fSize=14,fColor=(40969,65535,16385)
//    Button Autolycos_Stop,pos={213.60,160.80},size={69.60,30.60},proc=Button_StopTask,title="Stop"
//    Button Autolycos_Stop,font="Sylfaen",fSize=14,fColor=(65535,16385,16385)
//    SetVariable Autolycos_TimeResolution,pos={15.60,126.00},size={330.00,13.80},title="\\F'Sylfaen'Set the time resolution (in seconds) of the export:"
//    SetVariable Autolycos_TimeResolution,value= root:Autolycos:TimeRes
//    SetVariable Autolycos_PathToStore,pos={18.60,87.00},size={270.00,13.20},title="Select the path to store:"
//    SetVariable Autolycos_PathToStore,font="Sylfaen"
//    SetVariable Autolycos_PathToStore,limits={-inf,inf,0},value= root:Autolycos:OrgMx_PathName
//    Button Autolycos_Set_Path,pos={301.80,87.00},size={42.60,19.80},proc=Button_SetPath,title="Set"
//    Button Autolycos_Set_Path,font="Sylfaen"
    Button Autolycos_Credits,pos={345,15},size={54.60,19.80},proc=Button_Credits,title="Credits"
//    Button Autolycos_Credits,font="Sylfaen"
End Function


//------------------------------------------------------------------------------------------------//

function PrepTool()

	NewDataFolder/O/S root:Autolycos
	Variable/G Number
	//String/G ListOfStations="SIRTA;PuydeDome;Barcelona;Athens;Melpitz;Hyytiala;Kosetice;Other"
	String/G ListOfStations="AthensNOA;AthensDEM;ATOLL;Birkenes;Bologna;Cabauw;CAO;CeSMA;CIAO;Granada;HelsinkiSupersite;Hohenpeissenberg;Hylemossa;Hyytiälä;JFJ;Košetice;KuopioPiojo;Magurele;Manchester;Marseille;Melpitz;MonteCimone;Montseny;PalauReial;ParisBpEst;ParisChatelet;Payerne;PuydeDome;SIRTA;Taunus;UCD;Villum;Zeppelin;Other"
	String/G ToF_Quad_Str="UMR Quad;UMR ToF"
	String/G Lens_Str="PM1 Lens;PM2.5 Lens"
	String/G Vaporizer_Str="Standard Vap.;Capture Vap."
	String/G NextCloud_path="C:Users:acsm:Nextcloud:"
	String/G DryerStat_path="C:ACSM:DryerStats:"
	String/G Pump_path="C:ACSM:PumpData:"
	String/G SN_str=""
	Variable/G StartStop_bool=0
	Variable/G GeneratePMFInput=1
	Variable/G GenerateSoFi=1
	
	Make/N=1/O/T StationNameW,ToF_QuadW,LensW,VaporizerW
	
	NextCloud_path="C:Users:TofUser:NextCloud:"
	ToF_QuadW[0]="UMR ToF"
	SN_str=""
	
	
	string mzbool_str="0;0;0;0;0;0;0;0;0;0;0;1;1;0;1;1;1;1;0;0;0;0;0;1;1;1;1;0;1;1;1;0;0;0;0;0;1;1;0;0;1;1;1;1;1;0;0;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1"
	Make/O/N=100 mzbool
	variable i
	for(i=0;i<itemsinlist(mzbool_str);i+=1)
	mzbool[i]=str2num(stringfromlist(i,mzbool_str))
	endfor



//if (DataFolderExists("root:Autolycos")==0)
//SetDataFolder root:
//NewDataFolder/O/S Autolycos
//Variable/G TimeRes=0
//
//
//String/G OrgMx_PathName="Selected Folder"
//
//endif

	Autolycos_Panel()
	string SN
	prompt SN, "please enter the serial number of the instrument"
	doprompt "Warning", SN
	SN_str=SN
	
end

//------------------------------------------------------------------------------------------------//

Function Button_StopTask(ba) : ButtonControl
    STRUCT WMButtonAction &ba

    switch( ba.eventCode )
        case 2: // mouse up
            Button Autolycos_Start fColor=(40960,65280,16384)
            Button Autolycos_Stop fColor=(13056,0,0)
            StopAutolycosTask()
            break
        case -1: // control being killed
            break
    endswitch

    return 0
End


Function Button_StartTask(ba) : ButtonControl
    STRUCT WMButtonAction &ba

    switch( ba.eventCode )
        case 2: // mouse up
            Button Autolycos_Start fColor=(0,13056,0)
            Button Autolycos_Stop fColor=(65280,16384,16384)
            SVAR OrgMx_PathName=root:Autolycos:OrgMx_PathName
            NVAR TimeRes=root:Autolycos:TimeRes
            Autolycos()
            break
        case -1: // control being killed
            break
    endswitch

    return 0
End


Function Button_SetPath(Path_Name) : ButtonControl
String Path_name
    SVar OrgMx_PathName = root:Autolycos:OrgMx_PathName
    String temp_folder
    temp_folder = getdatafolder(1)
    
    //define path
    newpath/O/Q trajpath
    pathinfo trajpath
    OrgMx_PathName = S_path

    print OrgMx_PathName
    setdatafolder temp_folder
End


Function Button_Credits(ba) : ButtonControl
    STRUCT WMButtonAction &ba

    switch( ba.eventCode )
        case 2: // mouse up
            Execute "Credits_Autolycos()"
            break
        case -1: // control being killed
            break
    endswitch

    return 0
End

//------------------------------------------------------------------------------------------------//

Function Autolycos()

    SVAR OrgMx_PathName=root:Autolycos:OrgMx_PathName
    NewPath/O/C/Z PathFolder, OrgMx_PathName
    
    StartAutolycosTask()
end


//------------------------------------------------------------------------------------------------//

Function StartAutolycosTask()
    NVAR TimeRes=root:Autolycos:TimeRes 
    Variable numTicks = TimeRes * 60        // Run every x seconds. 1 tick =1/60 secondes (always seconds*60)
    CtrlNamedBackground Task_Autolycos, period=numTicks, proc=AutoSaveFile
    CtrlNamedBackground Task_Autolycos, start
End

Function StopAutolycosTask()
    CtrlNamedBackground Task_Autolycos, stop
End


//------------------------------------------------------------------------------------------------//

Function AutoSaveFile(s)        // This is the function that will be called periodically
    
    STRUCT WMBackgroundStruct &s
        
    //Date and Time of the wave to save
    
    //Variable/G WaveToSec =modDate(root:test:wave0)
    //Variable/G WaveToSec =CreationDate(root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSD_org)
    Variable/G WaveToSec =modDate(root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSD_org)
    //WaveToSec=WaveToSec-Date2Secs(-1,-1,-1)
    String/G TimeOfWave = Secs2Date(WaveToSec,-2) + "_" + Secs2Time(WaveToSec, 3)
    String/G TimeNow=replaceString(":",TimeOfWave,"_")
    print "Last AUTOLYCOS save: "+TimeNow
    
    
    //Calculate the error matrix
    Error_generate()
    
    //Define the name of matrix that will be saved
    String/G Mx_Org= "Mx_Org_"+TimeNow
    String/G Mx_NO3= "Mx_NO3_"+TimeNow
    String/G Mx_NH4= "Mx_NH4_"+TimeNow
    String/G Mx_SO4= "Mx_SO4_"+TimeNow
    String/G Mx_Chl= "Mx_Chl_"+TimeNow
    String/G Mx_Open= "Mx_Open_"+TimeNow
    String/G Mx_Close= "Mx_Close_"+TimeNow
    String/G Mx_Diff= "Mx_Diff_"+TimeNow
    
    //Define the error matrix 
    String/G Mx_Org_err= "Mx_err_Org_"+TimeNow
    String/G Mx_NO3_err= "Mx_err_NO3_"+TimeNow
    String/G Mx_NH4_err= "Mx_err_NH4_"+TimeNow
    String/G Mx_SO4_err= "Mx_err_SO4_"+TimeNow
    String/G Mx_Chl_err= "Mx_err_Chl_"+TimeNow
    
    //Define the Species and Specific Fragments
    String/G S_Org= "Org_"+TimeNow
    String/G S_NO3= "NO3_"+TimeNow
    String/G S_NH4= "NH4_"+TimeNow
    String/G S_SO4= "SO4_"+TimeNow
    String/G S_Chl= "Chl_"+TimeNow
    
    String/G S_f43= "f43_"+TimeNow
    String/G S_f44= "f44_"+TimeNow
    String/G S_f55= "f55_"+TimeNow
    String/G S_f57= "f57_"+TimeNow
    String/G S_f60= "f60_"+TimeNow
    
    
    //Duplicate all matrix
    Duplicate/O root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSD_org $Mx_Org
    Duplicate/O root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSD_no3 $Mx_NO3
    Duplicate/O root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSD_nh4 $Mx_NH4
    Duplicate/O root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSD_so4 $Mx_SO4
    Duplicate/O root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSD_chl $Mx_Chl
    Duplicate/O root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSO $Mx_Open
    Duplicate/O root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSC $Mx_Close
    Duplicate/O root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSD $Mx_Diff
    Duplicate/O root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSD_org Frags_Org
    Duplicate/O root:Packages:tw_IgorDAQ:ACSM:nativeTS:t_stop time_stop
    
    //Create Concentrations species + Specific Organic Fragments
    Variable LastTP= numpnts(time_Stop)-1
    Make/N=1/O TimePoint=time_Stop[LastTP]
    Make/N=1/O Org=sum($Mx_Org)
    Make/N=1/O NO3=sum($Mx_NO3)
    Make/N=1/O NH4=sum($Mx_NH4)
    Make/N=1/O SO4=sum($Mx_SO4)
    Make/N=1/O Chl=sum($Mx_Chl)
    
    Make/N=1/O f43=Frags_Org[42]/Org
    Make/N=1/O f44=Frags_Org[43]/Org
    Make/N=1/O f55=Frags_Org[54]/Org
    Make/N=1/O f57=Frags_Org[56]/Org
    Make/N=1/O f60=Frags_Org[59]/Org
    
    //Duplicate Species and Specific Fragments
    Duplicate/O Org $S_Org
    Duplicate/O NO3 $S_NO3
    Duplicate/O NH4 $S_NH4
    Duplicate/O SO4 $S_SO4
    Duplicate/O chl $S_chl
    
    Duplicate/O f43 $S_f43
    Duplicate/O f44 $S_f44
    Duplicate/O f55 $S_f55
    Duplicate/O f57 $S_f57
    Duplicate/O f60 $S_f60
    
    //Duplicate error matrix
    Wave Mx_err_Org, Mx_err_NO3, Mx_err_NH4, Mx_err_SO4, Mx_err_Chl
    Duplicate/O Mx_err_Org $Mx_Org_err
    Duplicate/O Mx_err_NO3 $Mx_NO3_err
    Duplicate/O Mx_err_NH4 $Mx_NH4_err
    Duplicate/O Mx_err_SO4 $Mx_SO4_err
    Duplicate/O Mx_err_Chl $Mx_Chl_err
    
    
    //****Save the data. NEED TO ADD THE TECHNICAL PARAMETERS AND SAVE 2 DIFFERENT FILES
    save/O/T/P=PathFolder $Mx_Org,$Mx_NO3,$Mx_NH4,$Mx_SO4,$Mx_Chl,$Mx_Open,$Mx_Close,$Mx_Diff,$Mx_Org_err,$Mx_NO3_err,$Mx_NH4_err,$Mx_SO4_err,$Mx_Chl_err,$S_Org,$S_NO3,$S_NH4,$S_SO4,$S_chl as TimeNow+".itx"
    //****Save the data in txt.
    save/O/J/W/P=PathFolder TimePoint,Org,NO3,NH4,SO4,chl,f43,f44,f55,f57,f60 as TimeNow+".txt"
    
    Killwaves/Z $Mx_Org,$Mx_NO3,$Mx_NH4,$Mx_SO4,$Mx_Chl,$Mx_Open,$Mx_Close,$Mx_Diff,$Mx_Org_err,$Mx_NO3_err,$Mx_NH4_err,$Mx_SO4_err,$Mx_Chl_err
    Killwaves/Z $S_Org,$S_NO3,$S_NH4,$S_SO4,$S_chl,$S_f43,$S_f44,$S_f55,$S_f57,$S_f60,Org,NO3,NH4,SO4,chl,f43,f44,f55,f57,f60, Frags_Org, time_stop,TimePoint

    return 0    // Continue background task
End

//------------------------------------------------------------------------------------------------//

Function Error_generate()
//**********MSSD WILL HAVE TO BE REPLACED BY THE TOTAL ERROR FOR PMF**********


//Import the required data
Duplicate/O root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSD MSSD
Duplicate/O root:Packages:tw_IgorDAQ:ACSM:nativeTS:params params
Duplicate/O root:Packages:tw_IgorDAQ:Batch:Chl_sparse Chl_sparse
Duplicate/O root:Packages:tw_IgorDAQ:Batch:NH4_sparse NH4_sparse
Duplicate/O root:Packages:tw_IgorDAQ:Batch:NO3_sparse NO3_sparse
Duplicate/O root:Packages:tw_IgorDAQ:Batch:Org_sparse Org_sparse
Duplicate/O root:Packages:tw_IgorDAQ:Batch:SO4_sparse SO4_sparse

//Define the variables used in the calculations 
Variable LastP=dimsize(params,0)-1

Variable RIE_Chl=params[LastP][9]
Variable RIE_NH4=params[LastP][10]
Variable RIE_NO3=params[LastP][11]
Variable RIE_Org=params[LastP][12]
Variable RIE_SO4=params[LastP][13]
Variable CE=params[LastP][20]
Variable IE=params[LastP][25]
Variable AB=params[LastP][27]
Variable Q_inlet=params[LastP][29]
Variable ABref=params[LastP][26]
Variable Chl_conc=params[LastP][4]


make/O/T/N=5 SparseList={"Chl_sparse","NH4_sparse","NO3_sparse","Org_sparse","SO4_sparse"}
make/O/T/N=5 SpeciesList={"Chl","NH4","NO3","Org","SO4"}
make/O/N=5 RIEList={RIE_Chl,RIE_NH4,RIE_NO3,RIE_Org,RIE_SO4}

Variable j
For (j=0;j<numpnts(SparseList);j=j+1)
    string SparseName= SparseList[j]
    wave Sparse_in = $SparseName

    string SpeciesName= SpeciesList[j]
    wave Species_in = $SpeciesName
    
    Variable RIE_in= RIEList[j]
    
//Application of the fragmentation table to the total mass spectra
    Duplicate/O MSSD MSSD_ion_err
    MSSD_ion_err=0
    
    //******PMF ERROR CALCULATION FROM JAY TO INCLUDE******

    Variable i 
    For (i=0; i<dimsize(Sparse_in,0);i=i+1)
        MSSD_ion_err[Sparse_in[i][1]]+=Sparse_in[i][2]*MSSD[Sparse_in[i][0]]
    endfor

//Convert ion/s to µg/m3
    Duplicate/O MSSD_ion_err MSSD_err

    MSSD_err= MSSD_ion_err * (1/(CE*IE*RIE_in)) * ((ABref)/(AB*Q_inlet))



    string rename_err =  "Mx_err_"+SpeciesName
    Duplicate/O MSSD_err, $rename_err
    print sum(MSSD_err)


endfor

//Clean a bit the folder
Killwaves/Z SparseList, SpeciesList, RIEList, MSSD_ion_err, MSSD_err

//Quick check of the diff between the given conc and the calculated conc for species...
wave Mx_err_Chl
print "Ratio is "
print (sum(Mx_err_Chl)/Chl_Conc)
print "Stop"

end

//------------------------------------------------------------------------------------------------//

//Credits Panel
Window Credits_Autolycos() : Panel
    PauseUpdate; Silent 1        // building window...
    NewPanel /K=1 /W=(112.8,118.8,450.6,309.6) as "Credits"
    ModifyPanel fixedSize=1
    ShowTools/A
    SetDrawLayer UserBack
    DrawLine 10,134,331,134
    TitleBox Credits_dev,pos={49.80,6.00},size={236.40,18.00},title="This toolkit was developped by "
    TitleBox Credits_dev,userdata(ResizeControlsInfo)= A"!!,D;!!#:B!!#B*!!#<Pz!!#](Aon\"Qzzzzzzzzzzzzzz!!#](Aon\"Qzz"
    TitleBox Credits_dev,userdata(ResizeControlsInfo) += A"zzzzzzzzzzzz!!#u:Du]k<zzzzzzzzzzz"
    TitleBox Credits_dev,userdata(ResizeControlsInfo) += A"zzz!!#u:Du]k<zzzzzzzzzzzzzz!!!"
    TitleBox Credits_dev,font="Arial",fSize=16,frame=0,fStyle=1
    TitleBox Credits_name,pos={144.60,36.60},size={55.80,16.20},title="Example"
    TitleBox Credits_name,userdata(ResizeControlsInfo)= A"!!,C,!!#=o!!#BCJ,hlcz!!#](Aon\"Qzzzzzzzzzzzzzz!!#](Aon\"Qzz"
    TitleBox Credits_name,userdata(ResizeControlsInfo) += A"zzzzzzzzzzzz!!#u:Du]k<zzzzzzzzzzz"
    TitleBox Credits_name,userdata(ResizeControlsInfo) += A"zzz!!#u:Du]k<zzzzzzzzzzzzzz!!!"
    TitleBox Credits_name,font="Arial",fSize=14,frame=0,fStyle=1
    TitleBox credits_Lab,pos={150.00,66.00},size={45.00,13.80},title="Example"
    TitleBox credits_Lab,userdata(ResizeControlsInfo)= A"!!,D#!!#??!!#B;J,hlSz!!#](Aon\"Qzzzzzzzzzzzzzz!!#](Aon\"Qzz"
    TitleBox credits_Lab,userdata(ResizeControlsInfo) += A"zzzzzzzzzzzz!!#u:Du]k<zzzzzzzzzzz"
    TitleBox credits_Lab,userdata(ResizeControlsInfo) += A"zzz!!#u:Du]k<zzzzzzzzzzzzzz!!!"
    TitleBox credits_Lab,font="Arial",fSize=12,frame=0
    TitleBox Credits_Team,pos={154.80,87.00},size={34.20,10.20},title="Example"
    TitleBox Credits_Team,userdata(ResizeControlsInfo)= A"!!,A^!!#?i!!#BW!!#<(z!!#](Aon\"Qzzzzzzzzzzzzzz!!#](Aon\"Qzz"
    TitleBox Credits_Team,userdata(ResizeControlsInfo) += A"zzzzzzzzzzzz!!#u:Du]k<zzzzzzzzzzz"
    TitleBox Credits_Team,userdata(ResizeControlsInfo) += A"zzz!!#u:Du]k<zzzzzzzzzzzzzz!!!"
    TitleBox Credits_Team,font="Arial",frame=0
    TitleBox Credits_Institution,pos={154.80,108.00},size={34.20,10.20},title="Example"
    TitleBox Credits_Institution,userdata(ResizeControlsInfo)= A"!!,F9!!#@<!!#@b!!#<(z!!#](Aon\"Qzzzzzzzzzzzzzz!!#](Aon\"Qzz"
    TitleBox Credits_Institution,userdata(ResizeControlsInfo) += A"zzzzzzzzzzzz!!#u:Du]k<zzzzzzzzzzz"
    TitleBox Credits_Institution,userdata(ResizeControlsInfo) += A"zzz!!#u:Du]k<zzzzzzzzzzzzzz!!!"
    TitleBox Credits_Institution,font="Arial",frame=0
    TitleBox Credits_contact,pos={150.00,141.00},size={37.80,10.80},title="\\f04\\f01Contacts"
    TitleBox Credits_contact,userdata(ResizeControlsInfo)= A"!!,G#!!#@s!!#>Z!!#<(z!!#](Aon\"Qzzzzzzzzzzzzzz!!#](Aon\"Qzz"
    TitleBox Credits_contact,userdata(ResizeControlsInfo) += A"zzzzzzzzzzzz!!#u:Du]k<zzzzzzzzzzz"
    TitleBox Credits_contact,userdata(ResizeControlsInfo) += A"zzz!!#u:Du]k<zzzzzzzzzzzzzz!!!"
    TitleBox Credits_contact,font="Arial",frame=0,fColor=(0,0,52224)
    TitleBox Credits_Mail2,pos={150.00,177.00},size={34.20,10.20},title="Example\\JC"
    TitleBox Credits_Mail2,userdata(ResizeControlsInfo)= A"!!,Eb!!#AY!!#A;!!#<(z!!#](Aon\"Qzzzzzzzzzzzzzz!!#](Aon\"Qzz"
    TitleBox Credits_Mail2,userdata(ResizeControlsInfo) += A"zzzzzzzzzzzz!!#u:Du]k<zzzzzzzzzzz"
    TitleBox Credits_Mail2,userdata(ResizeControlsInfo) += A"zzz!!#u:Du]k<zzzzzzzzzzzzzz!!!"
    TitleBox Credits_Mail2,font="Arial",frame=0,fColor=(0,0,65280)
    TitleBox Credits_Mail1,pos={150.00,162.00},size={34.20,10.20},title="Example\\JC"
    TitleBox Credits_Mail1,userdata(ResizeControlsInfo)= A"!!,E`!!#A3!!#A=!!#<(z!!#](Aon\"Qzzzzzzzzzzzzzz!!#](Aon\"Qzz"
    TitleBox Credits_Mail1,userdata(ResizeControlsInfo) += A"zzzzzzzzzzzz!!#u:Du]k<zzzzzzzzzzz"
    TitleBox Credits_Mail1,userdata(ResizeControlsInfo) += A"zzz!!#u:Du]k<zzzzzzzzzzzzzz!!!"
    TitleBox Credits_Mail1,font="Arial",frame=0,fColor=(0,0,65280)
    SetWindow kwTopWin,userdata(ResizeControlsInfo)= A"!!*'\"z!!#Bc!!#Aozzzzzzzzzzzzzzzzzzzzz"
    SetWindow kwTopWin,userdata(ResizeControlsInfo) += A"zzzzzzzzzzzzzzzzzzzzzzzzz"
    SetWindow kwTopWin,userdata(ResizeControlsInfo) += A"zzzzzzzzzzzzzzzzzzz!!!"
EndMacro





Function ACMCC_ToF_TriggeredExport()


	SetDataFolder root:Autolycos
	
	//Get Date
	Make/N=1/O/T ACSM_time
	//NVAR lastrow=root:Autolycos:Number
	wave DateW=root:Packages:tw_IgorDAQ:ACSM:nativeTS:t_stop
	WaveStats/Q DateW
	variable lastrow=V_maxloc
	
	string year=ACMCC_ExtractDateInfo(DateW[lastrow],"year")
	string month=ACMCC_ExtractDateInfo(DateW[lastrow],"month")
	string dayOfMonth=ACMCC_ExtractDateInfo(DateW[lastrow],"dayOfMonth")
	string hour=ACMCC_ExtractTimeInfo(DateW[lastrow],"hour")
	string minute=ACMCC_ExtractTimeInfo(DateW[lastrow],"minute")
	string second=ACMCC_ExtractTimeInfo(DateW[lastrow],"second")
	
	ACSM_time=year+"/"+month+"/"+dayofmonth+" "+hour+":"+minute+":"+second
	
	wave DataW=root:Packages:tw_IgorDAQ:ACSM:nativeTS:params
	
	//Get IE, RIE and CE values
	Make/N=1/D/O IE_NO3, RIE_NH4, RIE_SO4, RIE_NO3, RIE_OM, RIE_Cl, CE
	
	RIE_OM=DataW[lastrow][12]
	RIE_NO3=DataW[lastrow][11]
	RIE_SO4=DataW[lastrow][13]
	RIE_NH4=DataW[lastrow][10]
	RIE_Cl=DataW[lastrow][9]
	NVAR IE=root:Packages:tw_IgorDAQ:ACSM:ugConv_ionspg
	IE_NO3=IE
	CE=DataW[lastrow][20]
	
	
	
	//Get Concentrations
	Make/O/N=1 OM,NO3,SO4,NH4,Cl
	OM=DataW[lastrow][7]
	NO3=DataW[lastrow][6]
	SO4=DataW[lastrow][8]
	NH4=DataW[lastrow][5]
	Cl=DataW[lastrow][4]
	
	//Get Diagnostics
	Make/O/N=1 Airbeam, VapT, InletP
//	Make/O/N=1 RF, ChamberT, Airbeam, NewStart_Events, InletPClosed, InletPOpen, InletP, VapT
//	wave RFW=root:diagnostics:RF
//	wave ChamberTW=root:diagnostics:ChamberT
//	wave AirbeamW=DataW[lastrow][27]
//	wave NSE=root:diagnostics:NewStart_Events
//	wave IPC=root:diagnostics:InletPClosed
//	wave IPO=root:diagnostics:InletPOpen
//	wave IP=root:diagnostics:InletP
//	wave VapTW=root:diagnostics:VapT
//	
//	RF=RFW[lastrow]
//	ChamberT=ChamberTW[lastrow]
	Airbeam=DataW[lastrow][27]
//	NewStart_Events=NSE[lastrow]
//	InletPClosed=IPC[lastrow]
//	InletPOpen=IPO[lastrow]
	InletP=DataW[lastrow][29]
	VapT=DataW[lastrow][76]
	
	//Get Tuning Var
//	Make/O/N=1 EmCurrent, SEMVol, HeaterBias, VapV
//	wave DAQ=root:acsm_incoming:DAQ_Matrix
//	EmCurrent=DAQ[lastrow][6]
//	SEMVol=DAQ[lastrow][7]
//	HeaterBias=5 + DAQ[lastrow][2]*200/5
//	VapV=DAQ[lastrow][28]
	
	//Get f_Org & f_NO3 values
	Make/O/N=1 OM_f44, OM_f43, OM_f60, NO3_f30, NO3_f46
	wave MSSD_orgPMF=root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSD_orgPMF
	wave MSSD_no3=root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSD_no3
	OM_f44=MSSD_orgPMF[43]/sum(MSSD_orgPMF)
	OM_f43=MSSD_orgPMF[42]/sum(MSSD_orgPMF)
	OM_f60=MSSD_orgPMF[59]/sum(MSSD_orgPMF)
	NO3_f30=MSSD_no3[29]/sum(MSSD_no3)
	NO3_f46=MSSD_no3[45]/sum(MSSD_no3)
//	KillDataFolder root:ACMCC_Export:Temp
//	SetDataFolder root:ACMCC_Export

	//Get general info
//	Make/O/N=1/T acsm_local_version
	//acsm_local_version=versionStr
	Make/O/N=1/T export_ver
	export_ver=export_version
	Make/O/N=1/T SerialNumber
	SVAR/Z SN_str=root:Autolycos:SN_str
	SerialNumber=SN_str
//	wave DAQ=root:acsm_incoming:DAQ_Matrix
//	string temp_str
//	sprintf temp_str, "%6d",DAQ[lastrow][74]
//	SerialNumber=temp_str
	
	//Get Pump Diagnostics
//	SetDataFolder root:ACMCC_Export	
//	Make/O/N=1 TP1_S,TP1_W,TP1_T,TP2_S,TP2_W,TP2_T,TP3_S,TP3_W,TP3_T
	//ACMCC_PumpData()

	//Get Dryer Stats
//	SetDataFolder root:ACMCC_Export	
//	Make/O/N=1 Sampling_Flowrate, RH_In, RH_Out, T_In, T_Out
	//ACMCC_DryerStat_avg()
	
	
	
	//ACMCC_AutoPMFExport()
	//wave eOrg=root:PMFMats:eOrg
	//wave eNO3=root:PMFMats:eNO3
	//wave eSO4=root:PMFMats:eSO4
	//wave eNH4=root:PMFMats:eNH4
	//wave eChl=root:PMFMats:eChl
	SetDataFolder root:Autolycos	
	Make/O/N=1 OM_err,NO3_err,SO4_err,NH4_err,Cl_err
	OM_err=-999
	NO3_err=-999
	SO4_err=-999
	NH4_err=-999
	Cl_err=-999
	//duplicate/O eOrg, OM_err
	//duplicate/O eNO3, NO3_err
	//duplicate/O eSO4, SO4_err
	//duplicate/O eNH4, NH4_err
	//duplicate/O eChl, Cl_err
	
	//Create Table & Save
	variable i
	i=0
	string saveWavesList="ACSM_time;OM;NO3;SO4;NH4;Cl;IE_NO3;RIE_OM;RIE_NO3;RIE_SO4;RIE_NH4;RIE_Cl;CE;"
//	saveWavesList+="RF;ChamberT;Airbeam;NewStart_Events;InletPClosed;InletPOpen;InletP;VapT;"
	saveWavesList+="Airbeam;InletP;VapT;"
//	saveWavesList+="EmCurrent;SEMVol;HeaterBias;VapV;"
	saveWavesList+="OM_f44;OM_f43;OM_f60;NO3_f30;NO3_f46;"
	saveWavesList+="export_ver;"
//	saveWavesList+="TP1_S;TP1_W;TP1_T;TP2_S;TP2_W;TP2_T;TP3_S;TP3_W;TP3_T;"
//	saveWavesList+="Sampling_Flowrate;RH_In;RH_Out;T_In;T_Out;"
	saveWavesList+="OM_err;NO3_err;SO4_err;NH4_err;Cl_err;"
	
	
	SetDataFolder root:Autolycos
	for (i=0;i<itemsInList(saveWavesList);i+=1)
		wave w = $stringFromList(i,saveWavesList)
		if (i==0)
			Edit /N=ExportTable w
		else
			AppendToTable /W=ExportTable w
		endif
	endfor
	
	SetDataFolder root:Autolycos
	Wave/T SerialNumber
	Wave/T StationNameW
	
	string FileName=StationNameW[0]+"_ACSM-"+SerialNumber[0]+"_"
	FileName+=year+month+dayofmonth+hour+minute+".txt"
	
	SVAR/Z NextCloud_path=root:Autolycos:NextCloud_path
	string DataPathbis=NextCloud_path
	NewPath/Q/O/C SaveDataFilePathbis, DataPathbis
	DataPathbis+="ACMCC_Export:"
	NewPath/Q/O/C SaveDataFilePathbis, DataPathbis
	DataPathbis+=year+":"
	NewPath/Q/O/C SaveDataFilePathbis, DataPathbis
	DataPathbis+=month+":"
	NewPath/Q/O/C SaveDataFilePathbis, DataPathbis
	DataPathbis+=dayOfMonth+":"
	NewPath/Q/O/C SaveDataFilePathbis, DataPathbis
	
	ModifyTable/W=ExportTable format(ACSM_time)=8
	SaveTableCopy/O/T=1/W=ExportTable/P=SaveDataFilePathbis as FileName
	KillWindow ExportTable
	
	
	
	NVAR/Z GeneratePMFInput=root:Autolycos:GeneratePMFInput
	if (GeneratePMFInput==1)
		SetDataFolder root:Autolycos
		wave MSSD_orgPMF=root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSD_orgPMF
		wave MSSD_orgerr=root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSD_orgerr

		duplicate/O MSSD_orgPMF Org_Specs
		duplicate/O MSSD_orgerr Orgspecs_err
		
		Make/O/N=(numpnts(Org_Specs)) amus
		amus=p+1
		
		//wave Org_Specs,Orgspecs_err,amus
				
		Edit/N=PMFExportTable ACSM_time
		AppendToTable /W=PMFExportTable amus
		AppendToTable /W=PMFExportTable Orgspecs_err
		AppendToTable /W=PMFExportTable Org_Specs
		ModifyTable/W=PMFExportTable format(ACSM_time)=8
		
		FileName=StationNameW[0]+"_ACSM-"+SerialNumber[0]+"_"+"PMF_"+year+month+dayofmonth+hour+minute+".txt"
		saveTableCopy/O/T=1/W=PMFExportTable/P=SaveDataFilePathbis as FileName
		KillWindow PMFExportTable
	endif
	
	NVAR/Z GenerateSoFi=root:Autolycos:GenerateSoFi
	if (GenerateSoFi==1)
		ExportToFSoFi()	
	endif
	
	
	
End Function

Function/S ACMCC_ExtractDateInfo(dt,dateinfo)
	variable dt					// Input date/time value
 	string dateinfo
 	
	String shortDateStr = Secs2Date(dt, -1)		// <day-of-month>/<month>/<year> (<day of week>)
 
	Variable dayOfMonth, month, year, dayOfWeek
	sscanf shortDateStr, "%d/%d/%d (%d)", dayOfMonth, month, year, dayOfWeek
 	
 	string year_txt, month_txt, dayOfMonth_txt
 	
 	if (stringmatch(dateinfo,"year"))
 		year_txt=num2str(year)
 		return year_txt
 	elseif (stringmatch(dateinfo,"month"))
 		if (month<10)
 			month_txt="0"+num2str(month)
 		else
 			month_txt=num2str(month)
 		endif
 		return month_txt
 	elseif (stringmatch(dateinfo,"dayOfMonth"))
 		if (dayOfMonth < 10)
 			dayOfMonth_txt="0"+num2str(dayOfMonth)
 		else
 			dayOfMonth_txt=num2str(dayOfMonth)
 		endif
 		return dayOfMonth_txt
 	endif
End

Function/S ACMCC_ExtractTimeInfo(dt,timeinfo)
	variable dt
	string timeinfo
	
	variable time
	string hour, minute, second
	
	if (stringmatch(timeinfo,"hour"))
		time = mod(dt,24*60*60)
		if (trunc(time/3600) < 10)
			hour="0"+num2str(trunc(time/3600))
		else
			hour=num2str(trunc(time/3600))
		endif
 		return hour
 	elseif (stringmatch(timeinfo,"minute"))
 		time = mod(dt,3600)
 		if (trunc(time/60) < 10)
 			minute="0"+num2str(trunc(time/60))
 		else
 			minute=num2str(trunc(time/60))
 		endif
 		return minute
 	elseif (stringmatch(timeinfo,"second"))
 		time = mod(dt,60)
 		if (trunc(time) < 10)
 			second="0"+num2str(trunc(time))
 		else
 			second=num2str(trunc(time))
 		endif
 		return second
 	endif
	
End Function


Function ExportToFSoFi()

	SVAR/Z NextCloud_path=root:Autolycos:NextCloud_path
	string DataPathbis=NextCloud_path
	NewPath/Q/O/C SaveDataFilePathbis, DataPathbis
	DataPathbis+="SoFi:"
	NewPath/Q/O/C SaveDataFilePathbis, DataPathbis
	
	NewDataFolder/O/S root:Autolycos:SoFi
	wave DateW=root:Packages:tw_IgorDAQ:ACSM:nativeTS:t_stop
	WaveStats/Q DateW
	variable lastrow=V_maxloc
//	variable lastrow=numpnts(DateW)-1
	
	
	
	duplicate/O dateW aut
//	wave DateW=root:ACSM_Incoming:acsm_utc_time
//	variable lastrow=numpnts(DateW)-1
//	wave aut = root:acsm:file_fpfile_list_dat
//	duplicate/O aut alt
//	wave DAQ_Matrix = root:acsm_incoming:DAQ_Matrix
//	alt = -1*(DAQ_Matrix[p][51] * 3600) + aut
//	
	wave mzbool=root:Autolycos:mzbool
//	
//	wave chT = root:diagnostics:chamberT
//	wave ab = root:diagnostics:airbeam
//	wave ip = root:diagnostics:inletP
//	wave vt = root:diagnostics:vapT
//	wave/Z Org_pt = root:Time_Series:Org
//	wave/Z SO4_pt = root:Time_Series:SO4
//	wave/Z NO3_pt = root:Time_Series:NO3
//	wave/Z NH4_pt = root:Time_Series:NH4
//	wave/Z Chl_pt = root:Time_Series:Chl
//	wave/Z Masscalib_nitrate_pt = root:Masscalib_nitrate
//	
	wave MSSD_orgPMF=root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSD_orgPMF
	wave MSSD_orgerr=root:Packages:tw_IgorDAQ:ACSM:nativeTS:MSSD_orgerr

	duplicate/O/R=(0,99) MSSD_orgPMF Org_Specs
	duplicate/O/R=(0,99) MSSD_orgerr Orgspecs_err
		
	Make/O/N=(numpnts(Org_Specs)) amus
	amus=p+1


//	wave Org_Specs_pt=root:PMFMats:Org_Specs
//	wave amus_pt=root:PMFMats:amus
//	wave Orgspecs_err_pt=root:PMFMats:Orgspecs_err
//	
	string wlStr = "org_specs;orgSpecs_err;amus;acsm_utc_time"
//
	wave/T StationNameW=root:Autolycos:StationNameW
	wave/T SerialNumber=root:Autolycos:SerialNumber
//	
//	
	string dstr
	dstr = secs2date(aut[lastrow], -2)
	dstr = StationNameW[0]+"_ACSM-"+SerialNumber[0]+"_RTdata_" + dstr[0,3]+"_"+dstr[5,6]+"_"+dstr[8,9] + ".itx"
//	//dstr = "RTdata_" + dstr[0,3]+"_"+dstr[5,6]+"_"+dstr[8,9] + ".itx"
	GetFileFolderInfo /Z/Q/P=SaveDataFilePathbis dstr
//	
	if(V_flag != 0) //file doesn't exist- create waves for it and write them
		
		Extract/O Orgspecs_err, Orgspecs_err, mzbool==1
		Extract/O amus, amus, mzbool==1
		Extract/O Org_Specs, Org_Specs, mzbool==1
		
		MatrixOp /O Org_Specs = Org_Specs^t
		MatrixOp /O Orgspecs_err = Orgspecs_err^t
		
		make/D/O/N=1 acsm_utc_time; acsm_utc_time[0] = aut[lastrow]
		
		Save /B/P=SaveDataFilePathbis /T wlStr as dstr
		
	
	else //file exists - load in the data and append to it
		
		duplicate/O Org_Specs Org_Specs_temp
		duplicate/O Orgspecs_err Orgspecs_err_temp
		
		Extract/O Orgspecs_err_temp, Orgspecs_err_temp, mzbool==1
		Extract/O amus, amus, mzbool==1
		Extract/O Org_Specs_temp, Org_Specs_temp, mzbool==1
		
		MatrixOp /O Org_Specs_temp = Org_Specs_temp^t
		MatrixOp /O Orgspecs_err_temp = Orgspecs_err_temp^t
		
		loadwave/O/Q/T/P=SaveDataFilePathbis dstr

		wave/Z org_specs, orgSpecs_err,  acsm_utc_time
		variable n = numpnts(acsm_utc_time)
		insertPoints n, 1, org_specs, orgSpecs_err, acsm_utc_time
		org_specs[n][] = Org_Specs_temp[0][q]
		orgSpecs_err[n][] = Orgspecs_err_temp[0][q]
		acsm_utc_time[n] = aut[lastrow]

		save /B/O/P=SaveDataFilePathbis /T wlStr as dstr
	
	
	endif

End Function


Function StationInput_proc(name,num,str) : PopupMenuControl
	string name
	variable num
	string str

	SVAR/Z ListOfStations=root:Autolycos:ListOfStations

	wave/T StationNameW=root:Autolycos:StationNameW
	if (stringmatch(str,"other"))
		string temp
		string prompt_str="Please enter the name of the station. Be consistent with previous files !"
		prompt temp, prompt_str
		doprompt "Please verify", temp
		StationNameW[0]=temp
		ListOfStations+=";"+temp
		
	elseif(stringmatch(str,"select"))
		DoAlert/T="WARNING" 0,"Please select in the list the name of your station"
	else
		StationNameW[0]=str
	endif
End Function

Function/S InputLists(option)
	string option
	
	if (stringmatch(option,"Station"))
		SVAR/Z ListOfStations=root:Autolycos:ListOfStations
		return ListOfStations
	endif
	if (stringmatch(option,"Spectro"))
		SVAR/Z ToF_Quad_Str=root:Autolycos:ToF_Quad_Str
		return ToF_Quad_Str
	endif
	if (stringmatch(option,"Lens"))
		SVAR/Z Lens_Str=root:Autolycos:Lens_Str
		return Lens_Str
	endif
	if (stringmatch(option,"Vaporizer"))
		SVAR/Z Vaporizer_Str=root:Autolycos:Vaporizer_Str
		return Vaporizer_Str
	endif
	
End Function

Function LensInput_proc(name,num,str) : PopupMenuControl
	string name
	variable num
	string str

	wave/T LensW=root:Autolycos:LensW
	if(stringmatch(str,"select"))
		DoAlert/T="WARNING" 0,"Please select in the list"
	else
		LensW[0]=str
	endif
End Function

Function VapInput_proc(name,num,str) : PopupMenuControl
	string name
	variable num
	string str

	wave/T VaporizerW=root:Autolycos:VaporizerW
	if(stringmatch(str,"select"))
		DoAlert/T="WARNING" 0,"Please select in the list"
	else
		VaporizerW[0]=str
	endif
End Function

Function SetPath_proc(Path_name) : ButtonControl
	String Path_name
	SVAR/Z NextCloud_path=root:Autolycos:NextCloud_path
	
	String temp_folder
	temp_folder = getdatafolder(1)
	
	//define path
	newpath/O/Q path1
	pathinfo path1
	NextCloud_path = S_path
	setdatafolder temp_folder
end




Function LaunchExport(ctrlName) : ButtonControl
	string CtrlName	
	
	NVAR/Z StartStop_bool=root:Autolycos:StartStop_bool

	if (StartStop_bool==0)


		// Doing preliminary checks	
		SVAR NextCloud_path=root:Autolycos:NextCloud_path
		GetFileFolderInfo/Q/D/Z=1 NextCloud_path
		if(V_flag != 0 && V_flag!=-1)
			DoAlert/T="WARNING" 0,"NextCloud folder was not found on your computer. Please check."
			Abort
		endif
		
		wave/T StationNameW=root:Autolycos:StationNameW
		ControlInfo PM_Station
		if (stringmatch(S_Value,"select") && stringmatch(StationNameW[0],""))
			DoAlert/T="WARNING" 0,"Please set the name of the station"
			Abort
		endif
		
		ControlInfo PM_Lens
		if (stringmatch(S_Value,"select"))
			DoAlert/T="WARNING" 0,"Please set the type of lens"
			Abort
		endif
		
		ControlInfo PM_Vap
		if (stringmatch(S_Value,"select"))
			DoAlert/T="WARNING" 0,"Please set the type of vaporizer"
			Abort
		endif
		// End of preliminary checks

		
		NVAR Number=root:Autolycos:Number
		wave/T ToF_QuadW=root:Autolycos:ToF_QuadW
		wave ACSM_time=root:Packages:tw_IgorDAQ:ACSM:nativeTS:t_stop
		WaveStats/Q ACSM_time
		Number=v_max
		
		Button RunButton,title="STOP",pos={24,230},size={355,40},fSize=20,fstyle=1,fColor=(65280,16384,16384),proc=LaunchExport,font="Arial",disable=0
		StartStop_bool=1

		PopupMenu PM_Station disable = 2
		SetVariable PM_Spectro, disable = 2
		SetVariable Set_SN, disable=2
		SetVariable Set_SN, disable=2	
		PopupMenu PM_Lens, disable = 2
		PopupMenu PM_Vap, disable = 2
		CheckBox PMFBox, disable=2
		SetVariable Set_ExportPath,disable=2
		Button Set_PathToR_button,disable=2



		ACMCC_StartTask()

	elseif(StartStop_bool==1)
		
		StartStop_bool=0
		Button RunButton,title="START",pos={24,230},size={355,40},fSize=20,fstyle=1,fColor=(26112,52224,0),proc=LaunchExport,font="Arial",disable=0
		
		PopupMenu PM_Station disable = 0
		SetVariable PM_Spectro, disable = 0
		SetVariable Set_SN, disable=0
		SetVariable Set_SN, disable=0	
		PopupMenu PM_Lens, disable = 0
		PopupMenu PM_Vap, disable = 0
		CheckBox PMFBox, disable=0
		SetVariable Set_ExportPath,disable=0
		Button Set_PathToR_button,disable=0
		
		ACMCC_StopTask()
		
	endif

End Function


Function ACMCC_StartTask()
	Variable numTicks = 7200	//1 tick=1/60 s
	CtrlNamedBackground Test, period=numTicks, proc=ACMCC_Task
	CtrlNamedBackground Test, start
	
	NVAR/Z StartStop_bool=root:Autolycos:StartStop_bool
	StartStop_bool=1
	Button RunButton,title="STOP",pos={24,230},size={355,40},fSize=20,fstyle=1,fColor=(65280,16384,16384),proc=LaunchExport,font="Arial",disable=0
	
End


Function ACMCC_StopTask()
	CtrlNamedBackground Test, stop
	
	NVAR/Z StartStop_bool=root:Autolycos:StartStop_bool
	StartStop_bool=0
	Button RunButton,title="START",pos={24,230},size={355,40},fSize=20,fstyle=1,fColor=(26112,52224,0),proc=LaunchExport,font="Arial",disable=0
End



Function ACMCC_Task(s)   
	STRUCT WMBackgroundStruct &s
	
	NVAR Number=root:Autolycos:Number
	wave ACSM_time=root:Packages:tw_IgorDAQ:ACSM:nativeTS:t_stop
	SetDataFolder root:Autolycos
	duplicate/O ACSM_time temp
	WaveStats/Q temp
	//Number=v_max
	if (number<V_max)
		number=V_max
		ACMCC_ToF_TriggeredExport()
	endif
	
//	if (Number<numpnts(ACSM_time))
//			Number=numpnts(ACSM_time)
//			ACMCC_ToF_TriggeredExport()	//Export for ToF
//	endif
	return 0
End