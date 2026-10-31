#pragma TextEncoding = "UTF-8"
#pragma rtGlobals=3		// Use modern global access method and strict wave access.

StrConstant ACMCC_Export_version="1.1.1"


// History :
// ---------
//   v1.1 : 
//     - first official release
//
//   v1.1.1 : 2023/06/19
//     - date change from native data.
//     - standalone function to correct from previous data loading
//     - changed the name of Python script to be executed
/////////////////////////////////////////////////////////////


///////////////// MENU ////////////////////////////////////////

Menu "ACMCC Annual Submission"
	"Initialize Panel",/q,ACMCC_Initialize_Panel()
End

///////////////// END OF MENU ////////////////////////////////////////

Function ACMCC_Initialize_Panel()
	NewDataFolder/O/S root:ACMCC_Export
	Variable/G Number
	String/G ListOfStations="AthensNOA;AthensDEM;ATOLL;Birkenes;Bologna;Cabauw;CAO;CeSMA;CIAO;Granada;HelsinkiSupersite;Hohenpeissenberg;Hyltemossa;Hyytiala;JFJ;Kosetice;KuopioPiojo;Magurele;Manchester;Marseille;Melpitz;MonteCimone;Montseny;PalauReial;ParisBpEst;ParisChatelet;Payerne;PuydeDome;SIRTA;Taunus;UCD;Villum;Zeppelin;Other"
	String/G ToF_Quad_Str="UMR Quad;UMR ToF"
	String/G Lens_Str="PM1 Lens;PM2.5 Lens"
	String/G Vaporizer_Str="Standard Vap.;Capture Vap."
	String/G NextCloud_path=""
	String/G Script_path=""
	String/G Python_path=""

	String/G DryerStat_path="C:ACSM:DryerStats:"
	String/G Pump_path="C:ACSM:PumpData:"
	String/G SN_str=""
	
	String/G FileName_str=""
	String/G FlagName_str=""
	
	Variable/G StartStop_bool=0
	Variable/G GeneratePMFInput=1
	Variable/G ApplyMiddlebrook=0
	
	Make/N=1/O/T StationNameW,ToF_QuadW,LensW,VaporizerW
	
	NextCloud_path=""
	ToF_QuadW[0]="UMR ToF"
	SN_str=""
	
	Make/O/N=5/T ACSMvar
	Make/O/N=5 LOD
	
	ACSMvar[0]="OM"
	ACSMvar[1]="NO3"
	ACSMvar[2]="SO4"
	ACSMvar[3]="NH4"
	ACSMvar[4]="Cl"
	
	LOD[0]=0.1
	LOD[1]=0.12
	LOD[2]=0.28
	LOD[3]=0.51
	LOD[4]=0.1
	
	String/G TraceonGraph="OM"
	
	Variable/G AutoFlag_InletP=1
	Variable/G AutoFlag_InletPvar=1
	Variable/G AutoFlag_AB=1
	Variable/G AutoFlag_VapT=1
	Variable/G AutoFlag_ConcLOD=1
	Variable/G AutoFlag_Concvar=1
	Variable/G InletPmin=0
	Variable/G InletPmax=0
	Variable/G InletPvar=0.2
	Variable/G AB_warning=8.0e-06
	Variable/G AB_low=200000
	Variable/G AB_high=500000
	Variable/G Concvar=100
	Variable/G VapTmin=500
	Variable/G VapTmax=700
	
	Make/O/N=(2,3)/D CS_Bool
	CS_Bool[0][0]=56576
	CS_Bool[0][1]=56576
	CS_Bool[0][2]=56576
	CS_Bool[1][0]=36608
	CS_Bool[1][1]=3840
	CS_Bool[1][2]=3072
	
	String/G VarName="all;OM;NO3;SO4;NH4;Cl"
	String/G FlagList=""
	FlagList += "000: (V) Valid measurement;"
	FlagList += "100: (V) Checked by data originator. Valid measurement, overrides any invalid flags;"
	FlagList += "110: (V) Episode data checked and accepted by data originator. Valid measurement;"
	FlagList += "111: (V) Irregular data checked and accepted by data originator. Valid measurement;"
	FlagList += "456: (I) Invalidated by data originator;"
	FlagList += "559: (V) Unspecified contamination or local influence, but considered valid;"
	FlagList += "599: (I) Unspecified contamination or local influence ;"
	FlagList += "659: (I) Unspecified instrument/sampling anomaly;"
	FlagList += "660: (V) Unspecified instrument/sampling anomaly;"
	FlagList += "999: (I) Missing measurement, unspecified reason;"
	
	Variable/G YearToExport
	
	//Get IE, RIE and CE values
	Make/N=1/D/O IE_NO3, RIE_NH4, RIE_SO4, RIE_NO3, RIE_OM, RIE_Cl
	
//	FlagList += "-1: (?) Other flag - see EBAS website and enter at right;"
	
	ACMCC_Export_Panel()
	
End Function



Function ACMCC_Export_Panel()
	dowindow ExportPanel
	if(V_flag==1)
		killwindow ExportPanel
	endif
	
	newpanel/N=ExportPanel/W=(200,10,605,700)/K=1
	modifypanel fixedSize = 1
	
	SetDrawEnv fsize= 30,fstyle= 0,textrgb= (8704,8704,8704)
	DrawText 40,45,"ACSM Export Tool v."+ACMCC_Export_version
	
	PopupMenu PM_Station, fSize=14, pos={6,55}, size={100,20}, value = "select;"+InputLists("Station"), title="\f01Station Name", proc = StationInput_proc, disable = 0, win=ExportPanel,fstyle=1,font="Arial"	
	wave/T ToF_QuadW=root:ACMCC_Export:ToF_QuadW
	SetVariable PM_Spectro, fSize=14, pos={200,55}, size={180,20}, value = ToF_QuadW[0], title="\f01Spectrometer", disable = 0, win=ExportPanel,fstyle=0,font="Arial",noedit=1

	SVAR/Z SN_str=root:ACMCC_Export:SN_str
	SetVariable Set_SN, fSize=10, pos={230,80}, size={150,20}, value = SN_str, title="\f02Serial Number", win=ExportPanel,fstyle=2,font="Arial"

	if (stringmatch(ToF_QuadW[0],"UMR Quad"))
		SetVariable Set_SN, noedit=1
	elseif (stringmatch(ToF_QuadW[0],"UMR ToF"))
		SetVariable Set_SN, noedit=0
	endif
	
	PopupMenu PM_Lens, fSize=14, pos={6,120}, size={100,20}, value = "select;"+InputLists("Lens"), title="\f01Lens", proc = LensInput_proc, disable = 0, win=ExportPanel,fstyle=1,font="Arial"
	PopupMenu PM_Vap, fSize=14, pos={200,120}, size={100,20}, value = "select;"+InputLists("Vaporizer"), title="\f01Vaporizer", proc = VapInput_proc, disable = 0, win=ExportPanel,fstyle=1,font="Arial"

	SVAR/Z Script_path=root:ACMCC_Export:Script_path
	SetVariable Set_ScriptPath,title="Script Data Folder",pos={7,170},size={323,19},value=Script_path,fSize=12,noedit=1,font="Arial", disable=0
	Button Set_ScriptPath_button,title="\\f01SET",pos={336,170},size={50,20},fSize=14,fColor=(39168,39168,39168),font="Arial", proc=SetScriptPath_proc, disable=0
	
	//SVAR/Z NextCloud_path=root:ACMCC_Export:NextCloud_path
	//SetVariable Set_ExportPath,title="Save Data Folder",pos={7,170},size={323,19},value=NextCloud_path,fSize=12,noedit=1,font="Arial", disable=0
	//Button Set_PathToR_button,title="\\f01SET",pos={336,170},size={50,20},fSize=14,fColor=(39168,39168,39168),font="Arial", proc=SetPath_proc, disable=0
	
	GroupBox GetACSMconc,pos={2,210},size={395,135},title="\\f01I/ ACSM concentrations",fSize=12,fColor=(13056,4352,0),labelBack=(64512,64512,60160),frame=0,font="Arial"
	NVAR/Z ApplyMiddlebrook=root:ACMCC_Export:ApplyMiddlebrook
	//Button CheckCalibButton, title="\\f01Check calib. values", pos={10,230},fSize=14,size={150,25},font="Arial", fcolor=(52224,34816,0), proc=CheckCalibButton_proc
	Button CheckLODButton, title="\\f01 2.Check LOD values", pos={13,279},fSize=14,size={150,25},font="Arial", fcolor=(52224,34816,0), proc=CheckLODPanel
	//Button CalculateLODButton, title="\\f02Calculate LOD values", pos={210,255},fSize=10,size={125,15},font="Arial", fcolor=(52224,34816,0), proc=CalculateLODButton_proc
	CheckBox UseMiddlebrook_CB, title="Use Composition-Dependent CE", pos={175,281}, fsize=14,value=ApplyMiddlebrook, proc=CE_Warning_proc
	Button LoadACSMButt, title="\\f01 1.Load Native Files", pos={64,238},fSize=18,size={280,35},font="Arial", fcolor=(52224,34816,0), proc=LoadACSMDataFiles
	Button GetACSMButt, title="\\f01 3.Apply", pos={90,312},fSize=16,size={200,30},font="Arial", fcolor=(52224,34816,0), proc=GetACSM_proc

	Button GetDryerdata_butt, title="4.Dryer", pos={310,315}, size={60,25},font="Arial", fcolor=(52224,34816,0),proc=LoadDryerData, disable=2
	//Button GetPumpdata_butt, title="Pumps", pos={310,315}, size={60,25},font="Arial", fcolor=(52224,34816,0)
	
	GroupBox GetErrors,pos={2,350},size={395,80},title="\\f01II/ Errors",fSize=12,fColor=(13056,4352,0),labelBack=(61952,61952,65280),frame=0,font="Arial"
	//Button CalcErrorButt, title="\\f01Calculate Errors", pos={10,380},fSize=14,size={150,35},font="Arial", fcolor=(32768,40704,65280), proc=CalcError_proc
	//Button CheckErrorButt, title="\\f01Check Error Sanity", pos={200,380},fSize=14,size={150,35},font="Arial", fcolor=(32768,40704,65280), proc=CheckError_proc

	GroupBox GetFlags,pos={2,440},size={395,80},title="\\f01III/ Flags",fSize=12,fColor=(13056,4352,0),labelBack=(65280,59648,57600),frame=0,font="Arial"
	Button PreQualifButt, title="\\f01Suggest Flags", pos={10,470},fSize=14,size={150,35},font="Arial", fcolor=(65024,49152,43776), proc=AutoFlagPanel
	Button FlagPanelButt, title="\\f01Open Manual Flag Panel", pos={180,470},fSize=14,size={190,35},font="Arial", fcolor=(65024,49152,43776), proc=OpenFlagPanel_proc
	
	Button ExportButt, title="\\f01Export raw txt files", pos={10,550},fSize=14,size={385,35},font="Arial", fcolor=(43264,58112,43008), proc=ExportTxt_proc
	
	//SVAR/Z Script_path=root:ACMCC_Export:Script_path
	//SetVariable Set_ScriptPath,title="Script Data Folder",pos={7,630},size={323,19},value=Script_path,fSize=12,noedit=1,font="Arial", disable=0
	//Button Set_ScriptPath_button,title="\\f01SET",pos={336,630},size={50,20},fSize=14,fColor=(39168,39168,39168),font="Arial", proc=SetScriptPath_proc, disable=0
	
	//SVAR/Z Python_path=root:ACMCC_Export:Python_path
	//SetVariable Set_PythonPath,title="Python Data Folder",pos={7,660},size={323,19},value=Python_path,fSize=12,noedit=1,font="Arial", disable=0
	//Button Set_PythonPath_button,title="\\f01SET",pos={336,660},size={50,20},fSize=14,fColor=(39168,39168,39168),font="Arial", proc=SetPythonPath_proc, disable=0
	
	Button ExecuteScriptButt, title="\\f01Generate NASA-AMES", pos={10,620},fSize=14,size={385,35},font="Arial", fcolor=(39168,39168,39168), proc=ExecuteScript_proc
	
End


Function/S InputLists(option)
	string option
	
	if (stringmatch(option,"Station"))
		SVAR/Z ListOfStations=root:ACMCC_Export:ListOfStations
		return ListOfStations
	endif
	if (stringmatch(option,"Spectro"))
		SVAR/Z ToF_Quad_Str=root:ACMCC_Export:ToF_Quad_Str
		return ToF_Quad_Str
	endif
	if (stringmatch(option,"Lens"))
		SVAR/Z Lens_Str=root:ACMCC_Export:Lens_Str
		return Lens_Str
	endif
	if (stringmatch(option,"Vaporizer"))
		SVAR/Z Vaporizer_Str=root:ACMCC_Export:Vaporizer_Str
		return Vaporizer_Str
	endif
	
End Function


Function StationInput_proc(name,num,str) : PopupMenuControl
	string name
	variable num
	string str

	SVAR/Z ListOfStations=root:ACMCC_Export:ListOfStations

	wave/T StationNameW=root:ACMCC_Export:StationNameW
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

Function LensInput_proc(name,num,str) : PopupMenuControl
	string name
	variable num
	string str

	wave/T LensW=root:ACMCC_Export:LensW
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

	wave/T VaporizerW=root:ACMCC_Export:VaporizerW
	if(stringmatch(str,"select"))
		DoAlert/T="WARNING" 0,"Please select in the list"
	else
		VaporizerW[0]=str
	endif
	
	
	NVAR/Z ApplyMiddlebrook=root:ACMCC_Export:ApplyMiddlebrook
	
	if(stringmatch(VaporizerW[0],"Capture Vap."))
		ApplyMiddlebrook=0
		CheckBox UseMiddlebrook_CB, title="Use Composition-Dependent CE", fsize=14,value=ApplyMiddlebrook,disable=2
	elseif(stringmatch(VaporizerW[0],"Standard Vap."))
		ApplyMiddlebrook=1
		CheckBox UseMiddlebrook_CB, title="Use Composition-Dependent CE", fsize=14,value=ApplyMiddlebrook,disable=0
	
		
	endif
	
End Function


Function LoadACSMDataFiles(ctrlName) : ButtonControl
	string ctrlName
	
	NewDataFolder/O/S root:ToF_ACSM
	Variable refNum
	String message = "Select one or more files"
	String outputPaths
	//String fileFilters = "All Files:.*;"
	String fileFilters = "Data Files (*.txt,*.dat,*.csv):.txt,.dat,.csv;"

 
	Open /D /R /MULT=1 /F=fileFilters /M=message refNum
	outputPaths = S_fileName
 
	if (strlen(outputPaths) == 0)
		Print "Cancelled"

	else
		Variable numFilesSelected = ItemsInList(outputPaths, "\r")
		Variable i
		string nameofACSMfile
		for(i=0; i<numFilesSelected; i+=1)
			String path = StringFromList(i, outputPaths, "\r")

			LoadWave/Q/O/J/M/D/K=0/L={0,1,0,0,0}/V={","," $",0,0} path
			wave wave0
			nameofACSMfile="ACSM_"+num2str(i)
			Rename wave0,$nameofACSMfile
			
		endfor
		string ListofACSMWave=Wavelist("ACSM_*",";","")
		Concatenate/O/NP=0 ListofACSMWave, Mx
		
		KillListofWaves(ListofACSMWave)
		
		ConvertDateTime()
		CheckDoublonAndNaN()
		ConvertDateTime()
		MakeAllWaves()
				
	endif

End Function


Function ConvertDateTime()

	wave Mx=root:ToF_ACSM:Mx
	variable i
	
	make/O/T/N=(dimsize(Mx,0)) DateStrW
	make/O/D/N=(dimsize(Mx,0)) DateW
	
	DateStrW=juliantodate(datetojulian(Mx[p][0],1,1)+Mx[p][2]-1,1)

	Variable dayOfMonth, month, year, dayOfWeek
	string shortDateStr
	
	for(i=0;i<numpnts(DateStrW);i+=1)
		//shortDateStr=DateStrW[i]
		//sscanf shortDateStr, "%d/%d/%d", dayOfMonth, month, year
		//DateW[i]=date2secs(year,month,dayOfMonth)+(Mx[i][2]-trunc(Mx[i][2]))*(3600*24)
		DateW[i]=Mx[i][2]*86400 + date2secs(Mx[i][0],1,1) - 86400
	endfor

	SetScale d 0,0,"dat",DateW
	
End Function


Function MakeAllWaves()

	wave Mx=root:ToF_ACSM:Mx
	wave DateW=root:ToF_ACSM:DateW
	
	Make/O/N=(dimsize(Mx,0)) Status=Mx[p][3]
	Make/O/N=(dimsize(Mx,0)) Cl=Mx[p][4]
	Make/O/N=(dimsize(Mx,0)) NH4=Mx[p][5]
	Make/O/N=(dimsize(Mx,0)) NO3=Mx[p][6]
	Make/O/N=(dimsize(Mx,0)) OM=Mx[p][7]
	Make/O/N=(dimsize(Mx,0)) SO4=Mx[p][8]
	Make/O/N=(dimsize(Mx,0)) RIE_Cl=Mx[p][9]
	Make/O/N=(dimsize(Mx,0)) RIE_NH4=Mx[p][10]
	Make/O/N=(dimsize(Mx,0)) RIE_NO3=Mx[p][11]
	Make/O/N=(dimsize(Mx,0)) RIE_OM=Mx[p][12]
	Make/O/N=(dimsize(Mx,0)) RIE_SO4=Mx[p][13]
	Make/O/N=(dimsize(Mx,0)) f43=Mx[p][14]
	Make/O/N=(dimsize(Mx,0)) f44=Mx[p][15]
	Make/O/N=(dimsize(Mx,0)) f57=Mx[p][16]
	Make/O/N=(dimsize(Mx,0)) f60=Mx[p][17]
	Make/O/N=(dimsize(Mx,0)) HOA=Mx[p][18]
	Make/O/N=(dimsize(Mx,0)) OOA=Mx[p][19]
	Make/O/N=(dimsize(Mx,0)) CE=Mx[p][20]
	Make/O/N=(dimsize(Mx,0)) IE_ionspg=Mx[p][25]
	Make/O/N=(dimsize(Mx,0)) ABref=Mx[p][26]
	Make/O/N=(dimsize(Mx,0)) AB_total=Mx[p][27]
	Make/O/N=(dimsize(Mx,0)) AB_bg=Mx[p][28]
	Make/O/N=(dimsize(Mx,0)) Flow_css=Mx[p][29]
	Make/O/N=(dimsize(Mx,0)) Flow_p0=Mx[p][30]
	Make/O/N=(dimsize(Mx,0)) Flow_p1=Mx[p][31]
	Make/O/N=(dimsize(Mx,0)) n_total=Mx[p][32]
	Make/O/N=(dimsize(Mx,0)) n_bkgd=Mx[p][33]
	Make/O/N=(dimsize(Mx,0)) baseline=Mx[p][34]
	Make/O/N=(dimsize(Mx,0)) Threshold=Mx[p][35]
	Make/O/N=(dimsize(Mx,0)) mzCal_p1=Mx[p][36]
	Make/O/N=(dimsize(Mx,0)) mzCal_p2=Mx[p][37]
	Make/O/N=(dimsize(Mx,0)) ratio40div28=Mx[p][38]
	Make/O/N=(dimsize(Mx,0)) RBP=Mx[p][43]
	Make/O/N=(dimsize(Mx,0)) RG=Mx[p][44]
	Make/O/N=(dimsize(Mx,0)) Lens=Mx[p][45]
	Make/O/N=(dimsize(Mx,0)) Detector=Mx[p][46]
	Make/O/N=(dimsize(Mx,0)) HV_Spare=Mx[p][47]
	Make/O/N=(dimsize(Mx,0)) Pulser=Mx[p][48]
	Make/O/N=(dimsize(Mx,0)) Lens2=Mx[p][49]
	Make/O/N=(dimsize(Mx,0)) Defl=Mx[p][50]
	Make/O/N=(dimsize(Mx,0)) Defl_range=Mx[p][51]
	Make/O/N=(dimsize(Mx,0)) IonEx=Mx[p][52]
	Make/O/N=(dimsize(Mx,0)) Lens1=Mx[p][53]
	Make/O/N=(dimsize(Mx,0)) HB=Mx[p][54]
	Make/O/N=(dimsize(Mx,0)) IonChamber=Mx[p][55]
	Make/O/N=(dimsize(Mx,0)) Filament_V=Mx[p][56]
	Make/O/N=(dimsize(Mx,0)) Filament_Emm=Mx[p][57]
	Make/O/N=(dimsize(Mx,0)) Filament_I=Mx[p][58]
	Make/O/N=(dimsize(Mx,0)) Filament_N=Mx[p][59]
	Make/O/N=(dimsize(Mx,0)) Interlock=Mx[p][60]
	Make/O/N=(dimsize(Mx,0)) HVp=Mx[p][61]
	Make/O/N=(dimsize(Mx,0)) HVn=Mx[p][62]
	Make/O/N=(dimsize(Mx,0)) Turbo_speed=Mx[p][63]
	Make/O/N=(dimsize(Mx,0)) Turbo_power=Mx[p][64]
	Make/O/N=(dimsize(Mx,0)) Fore_pc=Mx[p][65]
	Make/O/N=(dimsize(Mx,0)) TPS_temp=Mx[p][66]
	Make/O/N=(dimsize(Mx,0)) Press_ioniser=Mx[p][67]
	Make/O/N=(dimsize(Mx,0)) Press_inlet=Mx[p][68]
	Make/O/N=(dimsize(Mx,0)) Heater_PWM=Mx[p][73]
	Make/O/N=(dimsize(Mx,0)) Heater_I=Mx[p][74]
	Make/O/N=(dimsize(Mx,0)) Heater_V=Mx[p][75]
	Make/O/N=(dimsize(Mx,0)) Heater_T=Mx[p][76]


	Display OM,NO3,SO4,NH4,Cl vs DateW
	ModifyGraph mode=7,hbFill=3,toMode=2,rgb(SO4)=(52428,1,1),rgb(OM)=(26205,52428,1),rgb(NO3)=(0,43690,65535),rgb(NH4)=(65535,43690,0),rgb(Cl)=(65535,32768,58981)
	Label bottom " "
	
End Function


Function KillListofWaves(ListofWave)
	string ListOfWave
	variable i
	Variable numFilesSelected = ItemsInList(ListOfWave, ";")
	for(i=0; i<numFilesSelected; i+=1)
		String Wave2Kill = StringFromList(i, ListOfWave, ";")
		KillWaves/Z $Wave2Kill	
	endfor
End Function


Function CheckLODPanel(ctrlName) : ButtonControl
	string ctrlName
	
	SetDataFolder root:ACMCC_Export
	
	//Get IE, RIE and CE values
	wave/T ACSMvar
	wave LOD

	wave ACSM_time=root:ToF_ACSM:DateW
	wave OM=root:ToF_ACSM:OM
	wave NO3=root:ToF_ACSM:NO3
	wave SO4=root:ToF_ACSM:SO4
	wave NH4=root:ToF_ACSM:NH4
	wave Cl=root:ToF_ACSM:Cl
	
	NewPanel/N=CheckLOD/W=(10,10,1200,400)/K=1
	Display/HOST=CheckLOD/W=(0.25,0.1,0.95,0.95) OM vs ACSM_time
	AppendToGraph NO3 vs ACSM_time
	AppendToGraph SO4 vs ACSM_time
	AppendToGraph NH4 vs ACSM_time
	AppendToGraph Cl vs ACSM_time
	ModifyGraph rgb(OM)=(26112,52224,0),rgb(NO3)=(0,43520,65280)
	ModifyGraph rgb(SO4)=(52224,0,0),rgb(NH4)=(65280,43520,0)
	ModifyGraph rgb(Cl)=(65280,16384,55552)
	Label bottom " "
	TextBox/C/B=1/N=text0/F=0/S=3/H={50,1,10}/A=MC "\\Z12\\f02draw a marquee on graph to select a period for LOD calculation"
	
	edit/HOST=CheckLOD/W=(0.01,0.1,0.23,0.6) ACSMvar,LOD

	Button DefaultLOD_but, title="Back to Default", pos={80,270}, size={130,25},fsize=14,font="Arial",proc=DefaultLOD_proc

End Function


Function DefaultLOD_proc(ctrlName) : ButtonControl
	string ctrlName
	SetDataFolder root:ACMCC_Export
	wave LOD
	LOD[0]=0.1
	LOD[1]=0.12
	LOD[2]=0.28
	LOD[3]=0.51
	LOD[4]=0.1
End Function

Function Calculate_LOD()

	SetDataFolder root:ACMCC_Export:
	wave OM=root:ToF_ACSM:OM
	wave NO3=root:ToF_ACSM:NO3
	wave SO4=root:ToF_ACSM:SO4
	wave NH4=root:ToF_ACSM:NH4
	wave Cl=root:ToF_ACSM:Cl
	wave ACSM_time=root:ToF_ACSM:DateW
	
	wave LOD=root:ACMCC_Export:LOD
	
	GetMarquee bottom
	variable MinIndex,MaxIndex
	MinIndex=BinarySearch(ACSM_time,V_left)
	MaxIndex=BinarySearch(ACSM_time,V_right)
	
	duplicate/O/R=(MinIndex,MaxIndex) OM, temp
	WaveStats/Q temp
	LOD[0]=3*V_sdev
	
	duplicate/O/R=(MinIndex,MaxIndex) NO3, temp
	WaveStats/Q temp
	LOD[1]=3*V_sdev
	
	duplicate/O/R=(MinIndex,MaxIndex) SO4, temp
	WaveStats/Q temp
	LOD[2]=3*V_sdev
	
	duplicate/O/R=(MinIndex,MaxIndex) NH4, temp
	WaveStats/Q temp
	LOD[3]=3*V_sdev
	
	duplicate/O/R=(MinIndex,MaxIndex) Cl, temp
	WaveStats/Q temp
	LOD[4]=3*V_sdev
	
End Function


Menu "GraphMarquee"
	"ACMCC: Calculate LOD from Marquee" , Calculate_LOD()
	"ACMCC: Set Threshold", Set_Threshold()
End


Function SetScriptPath_proc(Path_name) : ButtonControl
	String Path_name
	SVAR/Z Script_path=root:ACMCC_Export:Script_path
	
	String temp_folder
	temp_folder = getdatafolder(1)
	
	//define path
	newpath/O/Q path1
	pathinfo path1
	Script_path = S_path
	setdatafolder temp_folder
	
	wave/T StationNameW=root:ACMCC_Export:StationNameW
	//ControlInfo PM_Station
	//string station=S_value
	string station=StationNameW[0]
	string folder=Script_path+"data:"
	NewPath/C/O/Q tempPath folder
	folder=Script_path+"data:"+station
	NewPath/C/O/Q tempPath folder	//create this folder if it does not exits
	folder=Script_path+"data:"+station+":in:"
	NewPath/C/O/Q tempPath folder
	folder=Script_path+"data:"+station+":out:"
	NewPath/C/O/Q tempPath folder

	SVAR/Z NextCloud_path=root:ACMCC_Export:NextCloud_path
	NextCloud_path=Script_path+"data:"+station+":in:"
	
End Function


Function CE_Warning_proc(ctrlName,checked) : CheckBoxControl
	string ctrlName
	Variable checked
	
	if (checked==1)
		//DoAlert/T="WARNING" 0,"This will only calculate time-dependent CE. It will not correct concentrations. Please make sure that time dependent CE correction have not already been applied on your data"	
		DoAlert/T="WARNING" 0,"Raw data will be corrected from Composition-dependant CE"	
	endif

End Function


Function GetACSM_proc(ctrlName) : ButtonControl
	string ctrlName
	
	NVAR/Z ApplyMiddlebrook=root:ACMCC_Export:ApplyMiddlebrook
	SetDataFolder root:ACMCC_Export
	variable i
	wave DateW=root:ToF_ACSM:DateW
	//Make/N=(numpnts(DateW))/O ACSM_time
	//ACSM_time=DateW
	duplicate/O DateW, ACSM_time
	Make/N=(numpnts(DateW))/O/T ACSM_time_txt
	For (i=0;i<(numpnts(DateW));i+=1)
		string year=ACMCC_ExtractDateInfo(DateW[i],"year")
		string month=ACMCC_ExtractDateInfo(DateW[i],"month")
		string dayOfMonth=ACMCC_ExtractDateInfo(DateW[i],"dayOfMonth")
		string hour=ACMCC_ExtractTimeInfo(DateW[i],"hour")
		string minute=ACMCC_ExtractTimeInfo(DateW[i],"minute")
		string second=ACMCC_ExtractTimeInfo(DateW[i],"second")
	
		ACSM_time_txt[i]=year+"/"+month+"/"+dayofmonth+" "+hour+":"+minute+":"+second
	
	endfor	
	
	wave/T VaporizerW, LensW, ToF_QuadW
	string temp1=ToF_QuadW[0]
	string temp2=VaporizerW[0]
	string temp3=LensW[0]
	
	Make/O/T/N=(numpnts(DateW)) VaporizerW, LensW, ToF_QuadW
	ToF_QuadW=temp1
	VaporizerW=temp2
	LensW=temp3
	
	wave IE_NO3W=root:ToF_ACSM:IE_ionspg
	wave RIE_OMW=root:ToF_ACSM:RIE_OM
	wave RIE_NH4W=root:ToF_ACSM:RIE_NH4
	wave RIE_NO3W=root:ToF_ACSM:RIE_NO3
	wave RIE_SO4W=root:ToF_ACSM:RIE_SO4
	wave RIE_ClW=root:ToF_ACSM:RIE_Cl
	duplicate/O IE_NO3W IENO3
	duplicate/O RIE_NO3W RIE_NO3
	duplicate/O RIE_OMW RIE_OM
	duplicate/O RIE_NH4W RIE_NH4
	duplicate/O RIE_SO4W RIE_SO4
	duplicate/O RIE_ClW RIE_Cl
	
	wave CEW=root:ToF_ACSM:CE
	duplicate/O CEW CE
	
	wave OrgW=root:ToF_ACSM:OM
	wave NO3W=root:ToF_ACSM:NO3
	wave SO4W=root:ToF_ACSM:SO4
	wave NH4W=root:ToF_ACSM:NH4
	wave ClW=root:ToF_ACSM:Cl
	
	duplicate/O OrgW, OM
	duplicate/O NO3W, NO3
	duplicate/O NH4W, NH4
	duplicate/O SO4W, SO4
	duplicate/O ClW, Cl
	
	NVAR/Z ApplyMiddlebrook=root:ACMCC_Export:ApplyMiddlebrook
	if (ApplyMiddlebrook==1)
		wave LOD=root:ACMCC_Export:LOD
		Duplicate/o SO4 PredNH4, NH4_MeasToPredict, ANMF
		PredNH4=18*(SO4/96*2+NO3/62+Cl/35.45)
		NH4_MeasToPredict=NH4/PredNH4
		ANMF=(80/62)*NO3/(NO3+SO4+NH4+OM+Cl)
		For (i=0;i<(numpnts(SO4));i+=1)
			If (NH4_MeasToPredict[i]<0)
				NH4_MeasToPredict[i]=nan
			EndIf
			//	Nan ANMF points if negative or more than 1
			If (ANMF[i]<0)
				ANMF[i]=nan
			ElseIf (ANMF[i]>1)
				ANMF[i]=nan
			EndIf
			
			If (PredNH4[i]<LOD[3])
				CE[i]=0.5
			ElseIf (NH4_MeasToPredict[i]>=0.75)
				//	Apply Equation 4
				CE[i]= 0.0833+0.9167*ANMF[i]
			ElseIf (NH4_MeasToPredict[i]<0.75)
				//	Apply Equation 6
				CE[i]= 1-0.73*NH4_MeasToPredict[i]
			EndIf
		EndFor
		
		CE=min(1,(max(0.5,CE)))
		KillWaves ANMF, PredNH4, NH4_MeasToPredict 
		SO4*=CEW/CE
		NH4*=CEW/CE
		NO3*=CEW/CE
		Cl*=CEW/CE
		OM*=CEW/CE
	endif
	
	wave Mx=root:ToF_ACSM:Mx
	Make/O/N=(numpnts(DateW)) YearW, Start_DOY, Stop_DOY
	YearW=Mx[p][0]
	Start_DOY=Mx[p][1]
	Stop_DOY=Mx[p][2]
	
	duplicate/O root:ToF_ACSM:ABref ABref
	duplicate/O root:ToF_ACSM:AB_total AB_total
	duplicate/O root:ToF_ACSM:Flow_css Flow_css
	duplicate/O root:ToF_ACSM:n_total n_total
	duplicate/O root:ToF_ACSM:n_bkgd n_bkgd
	duplicate/O root:ToF_ACSM:baseline baseline
	duplicate/O root:ToF_ACSM:threshold threshold
	duplicate/O root:ToF_ACSM:mzCal_p1 mzCal_p1
	duplicate/O root:ToF_ACSM:mzCal_p2 mzCal_p2
	duplicate/O root:ToF_ACSM:ratio40div28 ratio40div28
	duplicate/O root:ToF_ACSM:mzCal_p1 mzCal_p1
	duplicate/O root:ToF_ACSM:Lens Lens
	duplicate/O root:ToF_ACSM:Pulser Pulser
	duplicate/O root:ToF_ACSM:Lens2 Lens2
	duplicate/O root:ToF_ACSM:IonEx IonEx
	duplicate/O root:ToF_ACSM:Lens1 Lens1
	duplicate/O root:ToF_ACSM:HB HB
	duplicate/O root:ToF_ACSM:IonChamber IonChamber
	duplicate/O root:ToF_ACSM:Filament_Emm Filament_Emm
	duplicate/O root:ToF_ACSM:Turbo_speed Turbo_speed
	duplicate/O root:ToF_ACSM:Turbo_power Turbo_power
	duplicate/O root:ToF_ACSM:Fore_pc Fore_pc
	duplicate/O root:ToF_ACSM:Press_inlet Press_inlet
	duplicate/O root:ToF_ACSM:Heater_PWM Heater_PWM
	duplicate/O root:ToF_ACSM:Heater_I Heater_I
	duplicate/O root:ToF_ACSM:Heater_V Heater_V
	duplicate/O root:ToF_ACSM:Heater_T Heater_T
	
	Make/O/N=(numpnts(DateW)) Servo2_PWM,Servo3_PWM
	Servo2_PWM=Mx[p][77]
	Servo3_PWM=Mx[p][78]
	
	
	//Get Dryer Stats
	SetDataFolder root:ACMCC_Export:
	Make/O/N=(numpnts(ACSM_time)) Sampling_Flowrate, RH_In, RH_Out, T_In, T_Out
	Sampling_Flowrate=9.999
	RH_In=99.999
	RH_Out=99.999
	T_In=99.999
	T_Out=99.999
	
	Make/O/N=(numpnts(ACSM_time)) OM_err, NO3_err, SO4_err, NH4_err, Cl_err
	OM_err=999.999
	NO3_err=999.999
	SO4_err=999.999
	NH4_err=999.999
	Cl_err=999.999
	
	Make/O/N=(numpnts(DateW)) numflag_OM
	duplicate/O numflag_OM numflag_NO3,numflag_SO4,numflag_NH4,numflag_Cl	
	Make/O/N=(numpnts(DateW)) ValidBool_OM=0
	duplicate/O ValidBool_OM ValidBool_NO3,ValidBool_SO4, ValidBool_NH4, ValidBool_Cl
	
	FindYearToExport()

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




Function LoadDryerData(ctrlName) : ButtonControl
	string ctrlName

	NewDataFolder/O/S root:ACMCC_Export:DryerStats
	Variable refNum
	String message = "Select one or more files"
	String outputPaths
	String fileFilters = "All Files:.*;"
 
	Open /D /R /MULT=1 /F=fileFilters /M=message refNum
	outputPaths = S_fileName
	
	if (strlen(outputPaths) == 0)
		Print "Cancelled"

	else
		Variable numFilesSelected = ItemsInList(outputPaths, "\r")
		Variable i
		string nameofDryerfile, nameOfDryerdate
		for(i=0; i<numFilesSelected; i+=1)
			String path = StringFromList(i, outputPaths, "\r")

			//LoadWave/Q/O/J/M/D/K=0/L={0,1,0,0,0}/V={" "," $",0,0} path
			//LoadWave/Q/O/J/M/D/K=0/L={0,1,0,0,0} path
			LoadWave /J/A/B="F=8,N=DateTimeW;F=0,N=InletP;F=0,N=CounterP;F=0,N=PDrop;F=0,N=FlowRate;F=0,N=RHIn;F=0,N=TIn;F=0,N=RHDry;F=0,N=TDry;"/L={0,1,0,0,0}/D/O/Q path
			wave DateTimeW,InletP,CounterP,PDrop,FlowRate,RHIn,TIn,RHDry,TDry	
			concatenate /NP/KILL {DateTimeW}, datW
			concatenate /NP/KILL {InletP}, InletPW
			concatenate /NP/KILL {CounterP}, CounterPW
			concatenate /NP/KILL {PDrop}, PDropW
			concatenate /NP/KILL {FlowRate}, FlowRateW
			concatenate /NP/KILL {RHIn}, RHInW
			concatenate /NP/KILL {TIn}, TInW		
			concatenate /NP/KILL {RHDry}, RHDryW
			concatenate /NP/KILL {TDry}, TDryW		
			
			//LoadWave/A=Dryertime_/Q/J/V={" "," $",0,0}/L={0,8,0,0,1}/R={French,2,2,2,1,"Year/Month/DayOfMonth",40} path
		endfor
		//string ListofDryerWave=Wavelist("Dryer_*",";","")
		//string ListofDateWave=Wavelist("Dryertime_*",";","")
		//Concatenate/O/NP=0 ListofDateWave, Dryerdate
		//Concatenate/O/NP=0 ListofDryerWave, Mx
		
		//KillListofWaves(ListofDryerWave)
		//KillListofWaves(ListofDateWave)
		
		wave ACSMtime=root:ACSM_Incoming:acsm_utc_time
		ACMCC_Avg_WaveList(datW,"InletPW;CounterPW;PDropW;FlowRateW;RHInW;TInW;RHDryW;TDryW",ACSMtime)
		wave InletPW_avg, CounterPW_avg, PDropW_avg, FlowRateW_avg, RHInW_avg, TInW_avg, RHDryW_avg, TDryW_avg
		InletPW_avg[numpnts(ACSMtime)-1]=NaN
		CounterPW_avg[numpnts(ACSMtime)-1]=NaN
		PDropW_avg[numpnts(ACSMtime)-1]=NaN
		FlowRateW_avg[numpnts(ACSMtime)-1]=NaN
		RHInW_avg[numpnts(ACSMtime)-1]=NaN
		TInW_avg[numpnts(ACSMtime)-1]=NaN
		RHDryW_avg[numpnts(ACSMtime)-1]=NaN
		TDryW_avg[numpnts(ACSMtime)-1]=NaN
		
		SetDataFolder root:ACMCC_Export:
		wave T_Out, T_In, RH_Out, RH_In, Sampling_Flowrate, ACSM_time
		T_Out=TDryW_avg
		T_In=TInW_avg
		RH_Out=RHDryW_avg
		RH_In=RHInW_avg
		Sampling_Flowrate=FlowRateW_avg
		
		 T_Out = (numtype(T_Out[p]) == 2) ? 0 : T_Out[p]
		 T_In = (numtype(T_In[p]) == 2) ? 0 : T_In[p]
		 RH_Out = (numtype(RH_Out[p]) == 2) ? 0 : RH_Out[p]
		 RH_In = (numtype(RH_In[p]) == 2) ? 0 : RH_In[p]
		 Sampling_Flowrate = (numtype(Sampling_Flowrate[p]) == 2) ? 0 : Sampling_Flowrate[p]
		
		Display RH_Out vs ACSM_time
		AppendToGraph RH_In vs ACSM_time
		ModifyGraph rgb(RH_Out)=(0,0,0)
	endif
	


End Function



Function ACMCC_Avg_WaveList(Date_Wave,ListOfWaves,Timeline)
	wave Date_Wave, Timeline
	string ListOfWaves
	
	variable nbelemlist=ItemsInList(ListofWaves)
	variable i
	string WaveNameToUse
	
	for(i=0;i<nbelemlist;i+=1)
		WaveNameToUse=StringFromList(i,ListofWaves)
		wave temp=$WaveNameToUse
		ACMCC_avg(temp, Date_Wave,Timeline)
	endfor
End Function



Function ACMCC_avg(Conc_Wave, Date_Wave,Timeline)
	wave Conc_Wave,Date_Wave,Timeline
	
	duplicate/O Conc_wave temp_conc
	duplicate/O Date_Wave, temp_date
	
	temp_date[]=(numtype(temp_conc[p])==2) ? NaN : temp_date[p]
	
	WaveTransform zapNaNs temp_date
	WaveTransform zapNaNs temp_conc
	
	string ConcWaveName=NameOfWave(Conc_Wave)+"_avg"
	Make/O/N=(numpnts(Timeline)) temp_avg
	variable i,j,k
	for (i=0;i<numpnts(Timeline)-1;i+=1)
		j=BinarySearch(temp_date,Timeline[i])
		k=BinarySearch(temp_date,Timeline[i+1])
		if (j==k)
			temp_avg[i]=nan
			continue
		endif
		temp_avg[i]=mean(temp_conc,j,k-1)
	endfor
	duplicate/O temp_avg $ConcWaveName
	KillWaves temp_avg,temp_conc,temp_date
End Function



Function AutoFlagPanel(ctrlName) : ButtonControl
	string ctrlName
	
	SetDataFolder root:ACMCC_Export:
	wave/T LensW
	
	NVAR/Z AutoFlag_InletP=root:ACMCC_Export:AutoFlag_InletP
	NVAR/Z AutoFlag_InletPvar=root:ACMCC_Export:AutoFlag_InletPvar
	NVAR/Z AutoFlag_AB=root:ACMCC_Export:AutoFlag_AB
	NVAR/Z AutoFlag_VapT=root:ACMCC_Export:AutoFlag_VapT
	NVAR/Z AutoFlag_ConcLOD=root:ACMCC_Export:AutoFlag_ConcLOD
	NVAR/Z AutoFlag_Concvar=root:ACMCC_Export:AutoFlag_Concvar
	
	NVAR/Z InletPmin=root:ACMCC_Export:InletPmin
	NVAR/Z InletPmax=root:ACMCC_Export:InletPmax
	NVAR/Z InletPvar=root:ACMCC_Export:InletPvar
	NVAR/Z AB_warning=root:ACMCC_Export:AB_warning
	NVAR/Z AB_low=root:ACMCC_Export:AB_low
	NVAR/Z AB_high=root:ACMCC_Export:AB_high
	NVAR/Z Concvar=root:ACMCC_Export:Concvar
	NVAR/Z VapTmin=root:ACMCC_Export:VapTmin
	NVAR/Z VapTmax=root:ACMCC_Export:VapTmax
	
	if(stringmatch(LensW[0],"PM1 Lens"))
		InletPmin=1.6
		InletPmax=2.5
	elseif(stringmatch(LensW[0],"PM2.5 Lens"))
		InletPmin=4.0
		InletPmax=4.8
	endif
	
	dowindow AutoFlagParam
	if(V_flag==1)
		killwindow AutoFlagParam
	endif
	
	newpanel/N=AutoFlagParam/W=(150,80,600,400)/K=1
	
	CheckBox InletP_CB, title="InletP", pos={10,10}, fsize=14, variable=AutoFlag_InletP
	SetVariable InletPmin_Var, title="min InletP", pos={90,10}, value=InletPmin, size={100,15}
	SetVariable InletPmax_Var, title="max InletP", pos={220,10}, value=InletPmax, size={100,15}
 	
 	CheckBox InletPvar_CB, title="InletP variation", pos={10,50}, fsize=14, variable=AutoFlag_InletPvar
 	SetVariable InletPvar_Var, title="abs threshold (torr)", pos={150,50}, value=InletPvar, size={150,15}
 	
 	CheckBox Airbeam_CB, title="Airbeam signal", pos={10,90}, fsize=14, variable=AutoFlag_AB
 	SetVariable AB_Warning_var, title="High limit AB", pos={150,90}, value=AB_high, size={140,15}
 	SetVariable AB_limit_var, title="Low limit AB", pos={295,90}, value=AB_low, size={140,15}

	CheckBox VapT_CB, title="Vap. temperature", pos={10,130}, fsize=14, variable=AutoFlag_VapT
 	SetVariable VapTmin_var, title="VapT min", pos={150,130}, value=VapTmin, size={100,15}
 	SetVariable VapTmax_var, title="VapT max", pos={270,130}, value=VapTmax, size={100,15}
 	
 	CheckBox ConcLOD_CB, title="Concentration LOD", pos={10,170}, fsize=14, variable=AutoFlag_ConcLOD
 	
 	CheckBox Concvar_CB, title="Concentration variation", pos={10,210}, fsize=14, variable=AutoFlag_Concvar
 	SetVariable Concvar_var, title="abs threshold", pos={190,210}, value=Concvar, size={120,15}
 	
 	Button AutoFlagButt, title="\\f01AutoFlag", pos={150,270},fSize=14,size={100,35},font="Arial", fcolor=(43264,58112,43008), proc=PreQualif_proc

End Function


Function PreQualif_proc(ctrlName) : ButtonControl
	string ctrlName
	killwindow AutoFlagParam
	
	SetDataFolder root:ACMCC_Export:
	wave ACSM_time
	wave OM, NO3, SO4, NH4,Cl, OM_err,NO3_err,SO4_err,NH4_err,Cl_err,numflag_OM,numflag_NO3,numflag_SO4,numflag_NH4,numflag_Cl
	wave LOD, Press_inlet, AB_total, Heater_T
	wave ValidBool_OM,ValidBool_NO3,ValidBool_SO4, ValidBool_NH4, ValidBool_Cl
	ValidBool_OM=0
	ValidBool_NO3=0
	ValidBool_SO4=0
	ValidBool_NH4=0
	ValidBool_Cl=0
	numflag_OM=0
	numflag_NO3=0
	numflag_SO4=0
	numflag_NH4=0
	numflag_Cl=0
	
	
	NVAR/Z AutoFlag_InletP=root:ACMCC_Export:AutoFlag_InletP
	NVAR/Z AutoFlag_InletPvar=root:ACMCC_Export:AutoFlag_InletPvar
	NVAR/Z AutoFlag_AB=root:ACMCC_Export:AutoFlag_AB
	NVAR/Z AutoFlag_VapT=root:ACMCC_Export:AutoFlag_VapT
	NVAR/Z AutoFlag_ConcLOD=root:ACMCC_Export:AutoFlag_ConcLOD
	NVAR/Z AutoFlag_Concvar=root:ACMCC_Export:AutoFlag_Concvar
	
	NVAR/Z InletPmin=root:ACMCC_Export:InletPmin
	NVAR/Z InletPmax=root:ACMCC_Export:InletPmax
	NVAR/Z InletPvar=root:ACMCC_Export:InletPvar
	//NVAR/Z AB_warning=root:ACMCC_Export:AB_warning
	NVAR/Z AB_low=root:ACMCC_Export:AB_low
	NVAR/Z AB_high=root:ACMCC_Export:AB_high
	NVAR/Z Concvar=root:ACMCC_Export:Concvar
	NVAR/Z VapTmin=root:ACMCC_Export:VapTmin
	NVAR/Z VapTmax=root:ACMCC_Export:VapTmax
	
	Make/O/N=(numpnts(OM)) AutoFlagBool_OM, AutoFlagBool_NO3, AutoFlagBool_SO4, AutoFlagBool_NH4, AutoFlagBool_Cl, OneWave
	AutoFlagBool_OM=NaN
	AutoFlagBool_NO3=NaN
	AutoFlagBool_SO4=NaN
	AutoFlagBool_NH4=NaN
	AutoFlagBool_Cl=NaN
	OneWave=1
	Make/O/N=7 AutoFlagNb
	Make/O/T/N=7 AutoFlagTxt
	
	AutoFlagNb=p
	AutoFlagTxt[0]="InletP out of boundaries"
	AutoFlagTxt[1]="InletP variation out of boundary"
	AutoFlagTxt[2]="Airbeam too low"
	AutoFlagTxt[3]="Airbeam too high"
	AutoFlagTxt[4]="VapT out of boundaries"
	AutoFlagTxt[5]="Concentration below -3*LOD"
	AutoFlagTxt[6]="Concentration variation out of boundary"
	
	Make/O/N=(7,3) AutoFlag_CB
	
	if (AutoFlag_InletP==1)
	
		numflag_OM[]=(Press_inlet[p]>InletPmax || Press_inlet[p]<InletPmin) ? 659 : numflag_OM[p]
		numflag_NO3[]=(Press_inlet[p]>InletPmax || Press_inlet[p]<InletPmin) ? 659 : numflag_NO3[p]
		numflag_SO4[]=(Press_inlet[p]>InletPmax || Press_inlet[p]<InletPmin) ? 659 : numflag_SO4[p]
		numflag_NH4[]=(Press_inlet[p]>InletPmax || Press_inlet[p]<InletPmin) ? 659 : numflag_NH4[p]
		numflag_Cl[]=(Press_inlet[p]>InletPmax || Press_inlet[p]<InletPmin) ? 659 : numflag_Cl[p]
		AutoFlagBool_OM[]=(Press_inlet[p]>InletPmax || Press_inlet[p]<InletPmin) ? 0 : AutoFlagBool_OM[p]
		AutoFlagBool_NO3[]=(Press_inlet[p]>InletPmax || Press_inlet[p]<InletPmin) ? 0 : AutoFlagBool_NO3[p]
		AutoFlagBool_SO4[]=(Press_inlet[p]>InletPmax || Press_inlet[p]<InletPmin) ? 0 : AutoFlagBool_SO4[p]
		AutoFlagBool_NH4[]=(Press_inlet[p]>InletPmax || Press_inlet[p]<InletPmin) ? 0 : AutoFlagBool_NH4[p]
		AutoFlagBool_Cl[]=(Press_inlet[p]>InletPmax || Press_inlet[p]<InletPmin) ? 0 : AutoFlagBool_Cl[p]
		
		Display Press_inlet vs ACSM_time
		Make/O/N=(numpnts(ACSM_time)) minInletPW, maxInletPW
		minInletPW=InletPmin
		maxInletPW=InletPmax
		AppendToGraph minInletPW vs ACSM_time
		AppendToGraph maxInletPW vs ACSM_time
		//SetAxis left 0.5,2.5
		ModifyGraph mode(minInletPW)=7,hbFill(minInletPW)=4,toMode(minInletPW)=1
		ModifyGraph rgb(minInletPW)=(32768,65280,32768)
		ModifyGraph rgb(maxInletPW)=(32768,65280,32768)
		ReorderTraces Press_inlet,{minInletPW,maxInletPW}
		ModifyGraph rgb(Press_inlet)=(0,0,0)
		Label bottom " "
		Label left "InletP (torr)"
		
	
		if(AutoFlag_InletPvar==1)
			
			ModifyGraph axisEnab(left)={0.51,1}
			
			duplicate/O Press_inlet d_press_inlet
			differentiate d_press_inlet
			
			numflag_OM[]=(abs(d_press_inlet[p])>InletPvar) ? 659 : numflag_OM[p]
			numflag_NO3[]=(abs(d_press_inlet[p])>InletPvar) ? 659 : numflag_NO3[p]
			numflag_SO4[]=(abs(d_press_inlet[p])>InletPvar) ? 659 : numflag_SO4[p]
			numflag_NH4[]=(abs(d_press_inlet[p])>InletPvar) ? 659 : numflag_NH4[p]
			numflag_Cl[]=(abs(d_press_inlet[p])>InletPvar) ? 659 : numflag_Cl[p]
			AutoFlagBool_OM[]=(abs(d_press_inlet[p])>InletPvar) ? 1 : AutoFlagBool_OM[p]
			AutoFlagBool_NO3[]=(abs(d_press_inlet[p])>InletPvar) ? 1 : AutoFlagBool_NO3[p]
			AutoFlagBool_SO4[]=(abs(d_press_inlet[p])>InletPvar) ? 1 : AutoFlagBool_SO4[p]
			AutoFlagBool_NH4[]=(abs(d_press_inlet[p])>InletPvar) ? 1 : AutoFlagBool_NH4[p]
			AutoFlagBool_Cl[]=(abs(d_press_inlet[p])>InletPvar) ? 1 : AutoFlagBool_Cl[p]
			
			Make/O/N=(numpnts(ACSM_time)) dInletP,dInletPthres
			dInletP[]=abs(d_press_inlet[p])
			dInletPthres=InletPvar
			AppendToGraph/R dInletP vs ACSM_time
			ModifyGraph rgb(dInletP)=(0,0,0)
			AppendToGraph/R dInletPthres vs ACSM_time
			ModifyGraph lstyle(dInletPthres)=3,lsize(dInletPthres)=3
			ModifyGraph rgb(dInletPthres)=(52224,0,0)
			ModifyGraph axisEnab(right)={0,0.49}
			Label right "\\F'Symbol'D\\F'Arial'InletP"
		endif
	endif
	
	if(AutoFlag_AB==1)
	
		numflag_OM[]=(AB_total[p]<AB_low) ? 659 : numflag_OM[p]
		numflag_NO3[]=(AB_total[p]<AB_low) ? 659 : numflag_NO3[p]
		numflag_SO4[]=(AB_total[p]<AB_low) ? 659 : numflag_SO4[p]
		numflag_NH4[]=(AB_total[p]<AB_low) ? 659 : numflag_NH4[p]
		numflag_Cl[]=(AB_total[p]<AB_low) ? 659 : numflag_Cl[p]
		AutoFlagBool_OM[]=(AB_total[p]<AB_low) ? 2 : AutoFlagBool_OM[p]
		AutoFlagBool_NO3[]=(AB_total[p]<AB_low) ? 2 : AutoFlagBool_NO3[p]
		AutoFlagBool_SO4[]=(AB_total[p]<AB_low) ? 2 : AutoFlagBool_SO4[p]
		AutoFlagBool_NH4[]=(AB_total[p]<AB_low) ? 2 : AutoFlagBool_NH4[p]
		AutoFlagBool_Cl[]=(AB_total[p]<AB_low) ? 2 : AutoFlagBool_Cl[p]
		
		numflag_OM[]=(AB_total[p]>AB_high) ? 659 : numflag_OM[p]
		numflag_NO3[]=(AB_total[p]>AB_high) ? 659 : numflag_NO3[p]
		numflag_SO4[]=(AB_total[p]>AB_high) ? 659 : numflag_SO4[p]
		numflag_NH4[]=(AB_total[p]>AB_high) ? 659 : numflag_NH4[p]
		numflag_Cl[]=(AB_total[p]>AB_high) ? 659 : numflag_Cl[p]
		AutoFlagBool_OM[]=(AB_total[p]>AB_high) ? 3 : AutoFlagBool_OM[p]
		AutoFlagBool_NO3[]=(AB_total[p]>AB_high) ? 3 : AutoFlagBool_NO3[p]
		AutoFlagBool_SO4[]=(AB_total[p]>AB_high) ? 3 : AutoFlagBool_SO4[p]
		AutoFlagBool_NH4[]=(AB_total[p]>AB_high) ? 3 : AutoFlagBool_NH4[p]
		AutoFlagBool_Cl[]=(AB_total[p]>AB_high) ? 3 : AutoFlagBool_Cl[p]
		
		
		Make/O/N=(numpnts(ACSM_time)) AB_lowW,AB_highW
		AB_lowW=AB_low
		AB_highW=AB_high

		Display AB_total vs ACSM_time
		AppendToGraph AB_lowW vs ACSM_time
		AppendToGraph AB_highW vs ACSM_time
		//SetAxis left 4e-08,*
		ModifyGraph mode(AB_lowW)=7,hbFill(AB_lowW)=4,toMode(AB_lowW)=1
		ModifyGraph rgb(AB_lowW)=(32768,65280,32768)
		ModifyGraph rgb(AB_highW)=(32768,65280,32768)
		ReorderTraces AB_total,{AB_lowW,AB_highW}
		Label bottom " "
		Label left "Airbeam signal"
		ModifyGraph rgb(AB_total)=(0,0,0)
	endif
	
	if(AutoFlag_VapT==1)
	
		numflag_OM[]=(Heater_T[p]>VapTmax || Heater_T[p]<VapTmin ) ? 660 : numflag_OM[p]
		numflag_NO3[]=(Heater_T[p]>VapTmax || Heater_T[p]<VapTmin ) ? 660 : numflag_NO3[p]
		numflag_SO4[]=(Heater_T[p]>VapTmax || Heater_T[p]<VapTmin ) ? 660 : numflag_SO4[p]
		numflag_NH4[]=(Heater_T[p]>VapTmax || Heater_T[p]<VapTmin ) ? 660 : numflag_NH4[p]
		numflag_Cl[]=(Heater_T[p]>VapTmax || Heater_T[p]<VapTmin ) ? 660 : numflag_Cl[p]
		AutoFlagBool_OM[]=(Heater_T[p]>VapTmax || Heater_T[p]<VapTmin ) ? 4 : AutoFlagBool_OM[p]
		AutoFlagBool_NO3[]=(Heater_T[p]>VapTmax || Heater_T[p]<VapTmin ) ? 4 : AutoFlagBool_NO3[p]
		AutoFlagBool_SO4[]=(Heater_T[p]>VapTmax || Heater_T[p]<VapTmin ) ? 4 : AutoFlagBool_SO4[p]
		AutoFlagBool_NH4[]=(Heater_T[p]>VapTmax || Heater_T[p]<VapTmin ) ? 4 : AutoFlagBool_NH4[p]
		AutoFlagBool_Cl[]=(Heater_T[p]>VapTmax || Heater_T[p]<VapTmin ) ? 4 : AutoFlagBool_Cl[p]
		
		Make/O/N=(numpnts(ACSM_time)) minVapT, maxVapT
		minVapT=VapTmin
		maxVapT=VapTmax
		Display minVapT vs ACSM_time
		AppendToGraph maxVapT vs ACSM_time
		AppendToGraph Heater_T vs ACSM_time
		ModifyGraph rgb(Heater_T)=(0,0,0)
		SetAxis left 400,*
		ModifyGraph mode(minVapT)=7,hbFill(minVapT)=4,toMode(minVapT)=1
		ModifyGraph rgb(minVapT)=(32768,65280,32768),rgb(maxVapT)=(32768,65280,32768)
		Label bottom " "
		Label left "Vaporizer temperature (°C)"
	endif
	
	if(AutoFlag_ConcLOD==1)
		numflag_OM[]=(OM[p]<(-3)*LOD[0]) ? 459 : numflag_OM[p]
		numflag_NO3[]=(NO3[p]<(-3)*LOD[1]) ? 459 : numflag_NO3[p]
		numflag_SO4[]=(SO4[p]<(-3)*LOD[2]) ? 459 : numflag_SO4[p]
		numflag_NH4[]=(NH4[p]<(-3)*LOD[3]) ? 459 : numflag_NH4[p]
		numflag_Cl[]=(Cl[p]<(-3)*LOD[4]) ? 459 : numflag_Cl[p]
		AutoFlagBool_OM[]=(OM[p]<(-3)*LOD[0]) ? 5 : AutoFlagBool_OM[p]
		AutoFlagBool_NO3[]=(NO3[p]<(-3)*LOD[1]) ? 5 : AutoFlagBool_NO3[p]
		AutoFlagBool_SO4[]=(SO4[p]<(-3)*LOD[2]) ? 5 : AutoFlagBool_SO4[p]
		AutoFlagBool_NH4[]=(NH4[p]<(-3)*LOD[3]) ? 5 : AutoFlagBool_NH4[p]
		AutoFlagBool_Cl[]=(Cl[p]<(-3)*LOD[4]) ? 5 : AutoFlagBool_Cl[p]
	endif
	
	if(AutoFlag_Concvar==1)
		duplicate/O OM d_OM
		duplicate/O NO3 d_NO3
		duplicate/O SO4 d_SO4
		duplicate/O NH4 d_NH4
		duplicate/O Cl d_Cl
		
		differentiate d_OM
		differentiate d_NO3
		differentiate d_SO4
		differentiate d_NH4
		differentiate d_Cl
	
		numflag_OM[]=(abs(d_OM[p])>Concvar) ? 659 : numflag_OM[p]
		numflag_NO3[]=(abs(d_NO3[p])>Concvar) ? 659 : numflag_NO3[p]
		numflag_SO4[]=(abs(d_SO4[p])>Concvar) ? 659 : numflag_SO4[p]
		numflag_NH4[]=(abs(d_NH4[p])>Concvar) ? 659 : numflag_NH4[p]
		numflag_Cl[]=(abs(d_Cl[p])>Concvar) ? 659 : numflag_Cl[p]
		AutoFlagBool_OM[]=(abs(d_OM[p])>Concvar) ? 6 : AutoFlagBool_OM[p]
		AutoFlagBool_NO3[]=(abs(d_NO3[p])>Concvar) ? 6 : AutoFlagBool_NO3[p]
		AutoFlagBool_SO4[]=(abs(d_SO4[p])>Concvar) ? 6 : AutoFlagBool_SO4[p]
		AutoFlagBool_NH4[]=(abs(d_NH4[p])>Concvar) ? 6 : AutoFlagBool_NH4[p]
		AutoFlagBool_Cl[]=(abs(d_Cl[p])>Concvar) ? 6 : AutoFlagBool_Cl[p]
	endif
	
	//ValidBool_OM[]=(flagOM[p]==459 || flagOM[p]==659) ? 1 : ValidBool_OM[p]
	ValidBool_OM[]=(numflag_OM[p]==456 || numflag_OM[p]==459 || numflag_OM[p]==460 || numflag_OM[p]==567 || numflag_OM[p]==568 || numflag_OM[p]==591 || numflag_OM[p]==593 || numflag_OM[p]==599 || numflag_OM[p]==635 || numflag_OM[p]==646 || numflag_OM[p]==659 || numflag_OM[p]==677 || numflag_OM[p]==899 || numflag_OM[p]==980 || numflag_OM[p]==999) ? 1 : ValidBool_OM[p]
	ValidBool_NO3[]=(numflag_NO3[p]==456 || numflag_NO3[p]==459 || numflag_NO3[p]==460 || numflag_NO3[p]==567 || numflag_NO3[p]==568 || numflag_NO3[p]==591 || numflag_NO3[p]==593 || numflag_NO3[p]==599 || numflag_NO3[p]==635 || numflag_NO3[p]==646 || numflag_NO3[p]==659 || numflag_NO3[p]==677 || numflag_NO3[p]==899 || numflag_NO3[p]==980 || numflag_NO3[p]==999) ? 1 : ValidBool_NO3[p]
	ValidBool_SO4[]=(numflag_SO4[p]==456 || numflag_SO4[p]==459 || numflag_SO4[p]==460 || numflag_SO4[p]==567 || numflag_SO4[p]==568 || numflag_SO4[p]==591 || numflag_SO4[p]==593 || numflag_SO4[p]==599 || numflag_SO4[p]==635 || numflag_SO4[p]==646 || numflag_SO4[p]==659 || numflag_SO4[p]==677 || numflag_SO4[p]==899 || numflag_SO4[p]==980 || numflag_SO4[p]==999) ? 1 : ValidBool_SO4[p]
	ValidBool_NH4[]=(numflag_NH4[p]==456 || numflag_NH4[p]==459 || numflag_NH4[p]==460 || numflag_NH4[p]==567 || numflag_NH4[p]==568 || numflag_NH4[p]==591 || numflag_NH4[p]==593 || numflag_NH4[p]==599 || numflag_NH4[p]==635 || numflag_NH4[p]==646 || numflag_NH4[p]==659 || numflag_NH4[p]==677 || numflag_NH4[p]==899 || numflag_NH4[p]==980 || numflag_NH4[p]==999) ? 1 : ValidBool_NH4[p]
	ValidBool_Cl[]=(numflag_Cl[p]==456 || numflag_Cl[p]==459 || numflag_Cl[p]==460 || numflag_Cl[p]==567 || numflag_Cl[p]==568 || numflag_Cl[p]==591 || numflag_Cl[p]==593 || numflag_Cl[p]==599 || numflag_Cl[p]==635 || numflag_Cl[p]==646 || numflag_Cl[p]==659 || numflag_Cl[p]==677 || numflag_Cl[p]==899 || numflag_Cl[p]==980 || numflag_Cl[p]==999) ? 1 : ValidBool_Cl[p]
	//ValidBool_NO3[]=(flagNO3[p]==459 || flagNO3[p]==659) ? 1 : ValidBool_NO3[p]
	//ValidBool_SO4[]=(flagSO4[p]==459 || flagSO4[p]==659) ? 1 : ValidBool_SO4[p]
	//ValidBool_NH4[]=(flagNH4[p]==459 || flagNH4[p]==659) ? 1 : ValidBool_NH4[p]
	//ValidBool_Cl[]=(flagCl[p]==459 || flagCl[p]==659) ? 1 : ValidBool_Cl[p]

	
End Function


Function OpenFlagPanel_proc(ctrlName) : ButtonControl
	string ctrlName
	
	dowindow FlagPanel
	if(V_flag==1)
		killwindow FlagPanel
	endif
	
	newpanel/N=FlagPanel/W=(150,80,2000,1000)/K=1

	SetDataFolder root:ACMCC_Export:
	wave ACSM_time, OM, NO3, SO4, NH4, Cl, numflag_OM,numflag_NO3,numflag_SO4,numflag_NH4,numflag_Cl,validbool_OM,validbool_NO3,validbool_SO4,validbool_nh4,validbool_Cl
	wave CS_bool
	wave OneWave, AutoFlagBool_OM, AutoFlagBool_NO3, AutoFlagBool_SO4, AutoFlagBool_NH4, AutoFlagBool_Cl
	Display/HOST=FlagPanel/W=(0.05,0.1,0.95,0.95)/L=L1 OM vs ACSM_time
	AppendToGraph/L=L2 NO3 vs ACSM_time
	AppendToGraph/L=L3 NH4 vs ACSM_time
	AppendToGraph/L=L4 SO4 vs ACSM_time
	AppendToGraph/L=L5 Cl vs ACSM_time
	ModifyGraph axisEnab(L1)={0,0.19},axisEnab(L2)={0.21,0.39}
	ModifyGraph axisEnab(L3)={0.41,0.59},axisEnab(L4)={0.61,0.79}
	ModifyGraph axisEnab(L5)={0.81,1},freePos(L1)={0,bottom},freePos(L2)={0,bottom}
	ModifyGraph freePos(L3)={0,bottom},freePos(L4)={0,bottom},freePos(L5)={0,bottom}
	Label bottom " "
	ModifyGraph rgb(OM)=(26112,52224,0)
	ModifyGraph rgb(NO3)=(0,34816,52224)
	ModifyGraph rgb(NH4)=(52224,0,0)
	ModifyGraph rgb(NH4)=(65280,43520,0),rgb(SO4)=(52224,0,0)
	ModifyGraph rgb(Cl)=(65280,32768,58880)
	AppendToGraph/R=R1 numflag_OM vs ACSM_time
	ModifyGraph axisEnab(R1)={0,0.19},freePos(R1)={0,kwFraction}
	ModifyGraph mode(numflag_OM)=1
	ModifyGraph zColor(numflag_OM)={ValidBool_OM,*,*,cindexRGB,0,CS_Bool}
	AppendToGraph/R=R2 numflag_NO3 vs ACSM_time
	AppendToGraph/R=R3 numflag_NH4 vs ACSM_time
	AppendToGraph/R=R4 numflag_SO4 vs ACSM_time
	AppendToGraph/R=R5 numflag_Cl vs ACSM_time
	ModifyGraph axisEnab(R2)={0.21,0.39},freePos(R2)={0,kwFraction}
	ModifyGraph mode(numflag_NO3)=1
	ModifyGraph zColor(numflag_NO3)={ValidBool_NO3,*,*,cindexRGB,0,CS_Bool}
	ModifyGraph axisEnab(R3)={0.41,0.59},freePos(R3)={0,kwFraction}
	ModifyGraph mode(numflag_NH4)=1
	ModifyGraph zColor(numflag_NH4)={ValidBool_NH4,*,*,cindexRGB,0,CS_Bool}
	ModifyGraph axisEnab(R4)={0.61,0.79},freePos(R4)={0,kwFraction}
	ModifyGraph mode(numflag_SO4)=1
	ModifyGraph zColor(numflag_SO4)={ValidBool_SO4,*,*,cindexRGB,0,CS_Bool}
	ModifyGraph axisEnab(R5)={0.81,1},freePos(R5)={0,kwFraction}
	ModifyGraph mode(numflag_Cl)=1
	ModifyGraph zColor(numflag_Cl)={ValidBool_Cl,*,*,cindexRGB,0,CS_Bool}
	
	ReorderTraces OM,{numflag_OM,numflag_NO3,numflag_NH4,numflag_SO4,numflag_Cl}
	
	ModifyGraph lsize(numflag_OM)=1.5,lsize(numflag_NO3)=1.5,lsize(numflag_NH4)=1.5, lsize(numflag_SO4)=1.5,lsize(numflag_Cl)=1.5
	
	AppendToGraph/R=R11 OneWave vs ACSM_time
	ModifyGraph axisEnab(R11)={0,0.19},freePos(R11)={0,kwFraction}
	ModifyGraph mode(OneWave)=2,lsize(OneWave)=6
	ModifyGraph axRGB(R11)=(65535,65535,65535),tlblRGB(R11)=(65535,65535,65535)
	ModifyGraph alblRGB(R11)=(65535,65535,65535)
	ModifyGraph zColor(OneWave)={AutoFlagBool_OM,0,6,EOSSpectral11,1}
	ModifyGraph axisEnab(R11)={0.17,0.19}
	ModifyGraph lsize(OneWave)=6
	
	AppendToGraph/R=R21 OneWave vs ACSM_time
	ModifyGraph axisEnab(R21)={0,0.19},freePos(R21)={0,kwFraction}
	ModifyGraph mode(OneWave#1)=2,lsize(OneWave#1)=6
	ModifyGraph axRGB(R21)=(65535,65535,65535),tlblRGB(R21)=(65535,65535,65535)
	ModifyGraph alblRGB(R21)=(65535,65535,65535)
	ModifyGraph zColor(OneWave#1)={AutoFlagBool_NO3,0,6,EOSSpectral11,1}
	ModifyGraph axisEnab(R21)={0.37,0.39}
	ModifyGraph lsize(OneWave#1)=6
	
	AppendToGraph/R=R31 OneWave vs ACSM_time
	ModifyGraph axisEnab(R31)={0,0.19},freePos(R31)={0,kwFraction}
	ModifyGraph mode(OneWave#2)=2,lsize(OneWave#2)=6
	ModifyGraph axRGB(R31)=(65535,65535,65535),tlblRGB(R31)=(65535,65535,65535)
	ModifyGraph alblRGB(R31)=(65535,65535,65535)
	ModifyGraph zColor(OneWave#2)={AutoFlagBool_NH4,0,6,EOSSpectral11,1}
	ModifyGraph axisEnab(R31)={0.57,0.59}
	ModifyGraph lsize(OneWave#2)=6
	
	AppendToGraph/R=R41 OneWave vs ACSM_time
	ModifyGraph axisEnab(R41)={0,0.19},freePos(R41)={0,kwFraction}
	ModifyGraph mode(OneWave#3)=2,lsize(OneWave#3)=6
	ModifyGraph axRGB(R41)=(65535,65535,65535),tlblRGB(R41)=(65535,65535,65535)
	ModifyGraph alblRGB(R41)=(65535,65535,65535)
	ModifyGraph zColor(OneWave#3)={AutoFlagBool_SO4,0,6,EOSSpectral11,1}
	ModifyGraph axisEnab(R41)={0.77,0.79}
	ModifyGraph lsize(OneWave#3)=6
	
	AppendToGraph/R=R51 OneWave vs ACSM_time
	ModifyGraph axisEnab(R51)={0,0.19},freePos(R51)={0,kwFraction}
	ModifyGraph mode(OneWave#4)=2,lsize(OneWave#4)=6
	ModifyGraph axRGB(R51)=(65535,65535,65535),tlblRGB(R51)=(65535,65535,65535)
	ModifyGraph alblRGB(R51)=(65535,65535,65535)
	ModifyGraph zColor(OneWave#4)={AutoFlagBool_SO4,0,6,EOSSpectral11,1}
	ModifyGraph axisEnab(R51)={0.97,0.99}
	ModifyGraph lsize(OneWave#4)=6
	
	TextBox/C/N=text1/F=0/A=MC "\\W516 InletP"
	TextBox/C/N=text1 "\\K(0,34816,52224)\\W516 InletP   \\K(0,43520,65280)\\W516 InletP variation   \\K(32768,54528,65280)\\W516 AB too low   \\K(57600,58112,39680)\\W51";DelayUpdate
	AppendText/N=text1 /NOCR "6AB low   \\K(65280,54528,32768)\\W516 VapT   \\K(52224,17408,0)\\W516 Conc < -3*LOD   \\K(39168,0,0)\\W516 Conc variation"
	
	
	PopupMenu FlagList_PUM title="\\f01Flag List",pos={10,10},value=FlagItemList(),fsize=18
	PopupMenu Var_PUM title="\\f01Apply on ",pos={10,50},value=VarItemList(),fsize=18
	Button ApplyFlag_Butt, title="\\f01Apply & Update", pos={250,40},fSize=14,size={150,35},font="Arial", fcolor=(43264,58112,43008),proc=ApplyFlag_proc
	CheckBox HideInvalid_CB, title="Hide Invalid", pos={425,50}, fsize=14,proc=HideInvalid_proc


	
End Function

Function/S FlagItemList()
	String list
	SVAR/Z FlagList=root:ACMCC_Export:FlagList
	list = FlagList
	return list
End

Function/S VarItemList()
	String list
	SVAR/Z VarName=root:ACMCC_Export:VarName
	list = VarName
	return list
End


Function HideInvalid_proc(ctrlName,checked) : CheckBoxControl
	string ctrlName
	variable checked
	//ControlInfo HideInvalid_CB
	//if(V_value==1)
	wave ACSM_time, OM, NO3, SO4, NH4, Cl, numflag_OM,numflag_NO3,numflag_SO4,numflag_NH4,numflag_Cl,validbool_OM,validbool_NO3,validbool_SO4,validbool_nh4,validbool_Cl
	wave CS_bool
	if (checked==1)
		duplicate/O OM OM_temp
		duplicate/O NO3 NO3_temp
		duplicate/O SO4 SO4_temp
		duplicate/O NH4 NH4_temp
		duplicate/O Cl Cl_temp
		
		OM_temp[]=(validbool_OM[p]==1) ? NaN : OM_temp[p]
		NO3_temp[]=(validbool_NO3[p]==1) ? NaN : NO3_temp[p]
		SO4_temp[]=(validbool_SO4[p]==1) ? NaN : SO4_temp[p]
		NH4_temp[]=(validbool_NH4[p]==1) ? NaN : NH4_temp[p]
		Cl_temp[]=(validbool_Cl[p]==1) ? NaN : Cl_temp[p]
		
		ReplaceWave trace= OM, OM_temp
		ReplaceWave trace= NO3, NO3_temp
		ReplaceWave trace= SO4, SO4_temp
		ReplaceWave trace= NH4, NH4_temp
		ReplaceWave trace= Cl, Cl_temp
		
		
	elseif(checked==0)
		wave OM_temp,NO3_temp,SO4_temp,NH4_temp,Cl_temp
		ReplaceWave trace= OM_temp, OM
		ReplaceWave trace= NO3_temp, NO3
		ReplaceWave trace= SO4_temp, SO4
		ReplaceWave trace= NH4_temp, NH4
		ReplaceWave trace= Cl_temp, Cl
	endif


End Function

Function ApplyFlag_proc(ctrlName) : ButtonControl
	string ctrlName
	ControlInfo FlagList_PUM
	string Flag_str=S_value
	string Flag_nb_str=flag_str[0,2]
	variable flag_nb_var=str2num(Flag_nb_str)
	
	string IsValid=flag_str[6,6]
	
	ControlInfo Var_PUM
	string Var_str=S_value

	SetDataFolder root:ACMCC_Export:
	wave ACSM_time,OM,NO3,NH4,SO4,Cl,numflag_OM,numflag_NO3,numflag_SO4,numflag_NH4,numflag_Cl,ValidBool_OM,ValidBool_NO3,ValidBool_SO4,ValidBool_NH4,ValidBool_Cl
	GetMarquee bottom
	variable MinIndex,MaxIndex
	MinIndex=BinarySearch(ACSM_time,V_left)
	MaxIndex=BinarySearch(ACSM_time,V_right)
	
	if(stringmatch(Var_str,"all"))
		numflag_OM[MinIndex,MaxIndex]=flag_nb_var
		numflag_NO3[MinIndex,MaxIndex]=flag_nb_var
		numflag_SO4[MinIndex,MaxIndex]=flag_nb_var
		numflag_NH4[MinIndex,MaxIndex]=flag_nb_var
		numflag_Cl[MinIndex,MaxIndex]=flag_nb_var
	
		if(stringmatch(IsValid,"V"))
			ValidBool_OM[MinIndex,MaxIndex]=0
			ValidBool_NO3[MinIndex,MaxIndex]=0
			ValidBool_SO4[MinIndex,MaxIndex]=0
			ValidBool_NH4[MinIndex,MaxIndex]=0
			ValidBool_Cl[MinIndex,MaxIndex]=0
			
		elseif(stringmatch(IsValid,"I"))
			ValidBool_OM[MinIndex,MaxIndex]=1
			ValidBool_NO3[MinIndex,MaxIndex]=1
			ValidBool_SO4[MinIndex,MaxIndex]=1
			ValidBool_NH4[MinIndex,MaxIndex]=1
			ValidBool_Cl[MinIndex,MaxIndex]=1
		endif
	elseif(stringmatch(Var_str,"OM"))
		numflag_OM[MinIndex,MaxIndex]=flag_nb_var
		if(stringmatch(IsValid,"V"))
			ValidBool_OM[MinIndex,MaxIndex]=0
		elseif(stringmatch(IsValid,"I"))
			ValidBool_OM[MinIndex,MaxIndex]=1
		endif
	elseif(stringmatch(Var_str,"NO3"))
		numflag_NO3[MinIndex,MaxIndex]=flag_nb_var
		if(stringmatch(IsValid,"V"))
			ValidBool_NO3[MinIndex,MaxIndex]=0
		elseif(stringmatch(IsValid,"I"))
			ValidBool_NO3[MinIndex,MaxIndex]=1
		endif
	elseif(stringmatch(Var_str,"SO4"))
		numflag_SO4[MinIndex,MaxIndex]=flag_nb_var
		if(stringmatch(IsValid,"V"))
			ValidBool_SO4[MinIndex,MaxIndex]=0
		elseif(stringmatch(IsValid,"I"))
			ValidBool_SO4[MinIndex,MaxIndex]=1
		endif
	elseif(stringmatch(Var_str,"NH4"))
		numflag_NH4[MinIndex,MaxIndex]=flag_nb_var
		if(stringmatch(IsValid,"V"))
			ValidBool_NH4[MinIndex,MaxIndex]=0
		elseif(stringmatch(IsValid,"I"))
			ValidBool_NH4[MinIndex,MaxIndex]=1
		endif
	elseif(stringmatch(Var_str,"Cl"))
		numflag_Cl[MinIndex,MaxIndex]=flag_nb_var
		if(stringmatch(IsValid,"V"))
			ValidBool_Cl[MinIndex,MaxIndex]=0
		elseif(stringmatch(IsValid,"I"))
			ValidBool_Cl[MinIndex,MaxIndex]=1
		endif
	endif

	//ControlInfo HideInvalid_CB
	//HideInvalid_proc("",V_value)	

End Function


Function Set_Threshold()
	string variable2use
	string varList="OM;NO3;NH4;SO4;Cl"
	
	prompt variable2use, "component:", popup, varList
	doprompt "On which component would you like to apply the threshold ?", variable2use

	variable axisNb=whichlistitem(variable2use,varList)+1
	string axis2use="L"+num2str(axisNb)
	
	SetDataFolder root:ACMCC_Export:
	wave ACSM_time
	wave Component = $variable2use
	wave numflag_component=$("numflag_"+variable2use)
	wave validBool_component=$("ValidBool_"+variable2use)
	
	GetMarquee $axis2use
	if(V_top>0)
		numflag_component[]=(Component[p]>V_top) ? 459 : numflag_component[p]
		ValidBool_component[]=(Component[p]>V_top) ? 1 : ValidBool_component[p]
	elseif(V_top<0)
		numflag_component[]=(Component[p]<V_top) ? 459 : numflag_component[p]
		ValidBool_component[]=(Component[p]<V_top) ? 1 : ValidBool_component[p]
	endif
End Function


Function FindYearToExport()

	NVAR/Z YearToExport=root:ACMCC_Export:YearToExport
	wave ACSM_time=root:ACMCC_Export:ACSM_time
	
	SetDataFolder root:ACMCC_Export:
	Make/O/N=(numpnts(ACSM_time)) YearW
	variable i
	for (i=0;i<numpnts(ACSM_time);i+=1)
		yearW[i]=ACMCC_year(ACSM_time[i])
	endfor
	
	
	variable nb_bins=max(2,wavemax(YearW)-wavemin(YearW))
	Make/O/N=(nb_bins) YearW_Hist,YearW_Occurence
	YearW_Hist[]=wavemin(YearW)+p
	
	Histogram/B={wavemin(YearW),1,nb_bins} YearW,YearW_Occurence
	
	WaveStats/Q YearW_Occurence
	YearToExport=YearW_Hist[V_maxRowLoc]
	

End Function


Function ACMCC_year(dt)
	variable dt					// Input date/time value
 
	String shortDateStr = Secs2Date(dt, -1)		// <day-of-month>/<month>/<year> (<day of week>)
 
	Variable dayOfMonth, month, year, dayOfWeek
	sscanf shortDateStr, "%d/%d/%d (%d)", dayOfMonth, month, year, dayOfWeek
 
	return year
End


Function ExportTxt_proc(CtrlName) : ButtonControl
	string ctrlName
	
	variable i
	i=0
	
	SVAR/Z FileName_str=root:ACMCC_Export:FileName_str
	SVAR/Z FlagName_str=root:ACMCC_Export:FlagName_str
	
	SetDataFolder root:ACMCC_Export
	string saveWavesList="ACSM_time_txt;OM;NO3;SO4;NH4;Cl;IENO3;RIE_OM;RIE_NO3;RIE_SO4;RIE_NH4;RIE_Cl;"
	saveWavesList+="ABref;AB_total;Flow_css;n_total;n_bkgd;baseline;threshold;mzCal_p1;mzCal_p2;"
	saveWavesList+="ratio40div28;Lens;Pulser;Lens2;IonEx;Lens1;HB;IonChamber;Filament_Emm;"
	saveWavesList+="Turbo_speed;Turbo_power;Fore_pc;Press_inlet;Heater_PWM;Heater_I;Heater_V;Heater_T;"
	saveWavesList+="Sampling_Flowrate;RH_In;RH_Out;T_In;T_Out;"
	saveWavesList+="OM_err;NO3_err;SO4_err;NH4_err;Cl_err;"
	saveWavesList+="Tof_QuadW;LensW;VaporizerW;"
	
	SetDataFolder root:ACMCC_Export
	wave/T VaporizerW,LensW,ToF_QuadW,StationNameW,ACSM_time_txt
	SVAR/Z SN_str=root:ACMCC_Export:SN_str
	NVAR/Z YearToExport=root:ACMCC_Export:YearToExport
	string filename=StationNameW[0]+"_ACSM-"+SN_str+"_"+num2str(YearToExport)+".txt"
	FileName_str=filename
	string Flagfilename=StationNameW[0]+"_ACSM-"+SN_str+"_FLAGS_"+num2str(YearToExport)+".txt"
	FlagName_str=Flagfilename
	SVAR/Z NextCloud_path=root:ACMCC_Export:NextCloud_path
	NewPath/O/Q SaveFolderPath, NextCloud_path
	
	for (i=0;i<itemsInList(saveWavesList);i+=1)
		wave w = $stringFromList(i,saveWavesList)
		if (i==0)
			Edit /N=ExportTable w
		else
			AppendToTable /W=ExportTable w
		endif
	endfor
	//ModifyTable/W=ExportTable format(ACSM_time)=8
	ModifyTable title(ACSM_time_txt)="ACSM_time"
	saveTableCopy/O/T=1/P=SaveFolderPath/W=ExportTable as filename
	KillWindow ExportTable
	
	saveWavesList=""
	saveWavesList+="ACSM_time_txt;numflag_OM;numflag_NO3;numflag_SO4;numflag_NH4;numflag_Cl;"
	for (i=0;i<itemsInList(saveWavesList);i+=1)
		wave w = $stringFromList(i,saveWavesList)
		if (i==0)
			Edit /N=FlagTable w
		else
			AppendToTable /W=FlagTable w
		endif
	endfor
	//ModifyTable/W=FlagTable format(ACSM_time)=8
	ModifyTable title(ACSM_time_txt)="ACSM_time"
	saveTableCopy/O/T=1/P=SaveFolderPath/W=FlagTable as Flagfilename
	KillWindow FlagTable


End Function


Function ExecuteScript_proc(ctrlName) : ButtonControl
	string ctrlName
	
	SVAR/Z FileName_str=root:ACMCC_Export:FileName_str
	SVAR/Z FlagName_str=root:ACMCC_Export:FlagName_str
	SVAR/Z NextCloud_path=root:ACMCC_Export:NextCloud_path
	SVAR/Z Script_path=root:ACMCC_Export:Script_path
	SVAR/Z Python_path=root:ACMCC_Export:Python_path
	
	string ParsedScript_path=ParseFilePath(5,Script_path,"\\",0,0)
	
	wave/T StationNameW=root:ACMCC_Export:StationNameW
	string station=StationNameW[0]
	
	string Batch_str=""
	Batch_str+="@echo off;"
	Batch_str+="REM set conda_root='C:\Users\jepetit\Anaconda3\';"
	Batch_str+="REM echo '- load conda env -';"
	Batch_str+="REM call %conda_root%\Scripts\activate.bat %conda_root%;"
	Batch_str+="echo '- start process -';"
	Batch_str+="cd " + ParsedScript_path+";"
	Batch_str+="python src\\rawto012.py data\\" +station
	Batch_str+="\\in\\" + FileName_str
	Batch_str+=" data\\" +station
	Batch_str+="\\in\\" + FlagName_str
	Batch_str+=" data\\" +station
	Batch_str+="\\out\\;"
	
	
	//Batch_str+="python src\rawto012.py tests\SIRTA\in\SIRTA_ACSM-140113_2021.txt tests\SIRTA\in\SIRTA_ACSM-140113_FLAGS_2021.txt tests\SIRTA\out\;"
	Batch_str+="pause;"
	
	
	//Batch_str+="cd " + Script_path+";"
	//Batch_str+="py src/rawto012.py "+NextCloud_path+FileName_str+" "+NextCloud_path+FileName_str+" ~/test;"
	//Batch_str+="pause"
	Make/T/O/N=(ItemsInList(batch_str, ";")) batch_txt
	batch_txt = StringFromList(p, batch_str, ";")
	
	Newpath/O/Q BatchPath, Script_path
	Save/T/G/O/M="\r\n"/P=BatchPath Batch_txt as "ACSM_converter.bat"
	
	//executescripttext/Z/B "\"C:\\Users\\jepetit\\Downloads\\actris_acsm_converter-master\\ACSM_converter.bat"
	
	string batch_path=ParsedScript_path+"ACSM_converter.bat"
	
	string batch_txt1
	//sprintf batch_txt1, "cmd.exe /C \"%s\"", "C:\Users\jepetit\Downloads\actris_acsm_converter-master\ACSM_converter.bat"
	sprintf batch_txt1, "cmd.exe /C \"%s\"", batch_path
	
	executescripttext/Z/B batch_txt1
	
	
End Function


Function CheckDoublonAndNaN()

	SetDataFolder root:ToF_ACSM
	wave DateW, Mx
	Make/O/N=(numpnts(DateW)) d_date
	
	d_date[0]=999
	
	variable i
	for(i=1;i<numpnts(DateW);i+=1)
		d_date[i]=DateW[i]-DateW[i-1]
	endfor

	d_date[]=(numtype(DateW[p])==2) ? 0 : d_date[p]
	
	d_date[]=(d_date[p]!=0) ? 1 : d_date[p]
	
	if (sum(d_date)!=numpnts(d_date))
		Extract/O Mx, Mx_corr, (d_date[p]!=0)
		Redimension/N=(sum(d_date),dimsize(Mx,1)) Mx_corr
	
		duplicate/O Mx_corr, Mx
	endif

End Function


Function Standalone_CorrectDate()

	SetDataFolder root:ACMCC_Export
	wave ACSM_time
	variable i
	wave DateW=root:ToF_ACSM:DateW
	
	if (dimsize(DateW,0)==dimsize(ACSM_time,0))
	
		duplicate/O DateW, ACSM_time
		Make/N=(numpnts(DateW))/O/T ACSM_time_txt
		For (i=0;i<(numpnts(DateW));i+=1)
			string year=ACMCC_ExtractDateInfo(DateW[i],"year")
			string month=ACMCC_ExtractDateInfo(DateW[i],"month")
			string dayOfMonth=ACMCC_ExtractDateInfo(DateW[i],"dayOfMonth")
			string hour=ACMCC_ExtractTimeInfo(DateW[i],"hour")
			string minute=ACMCC_ExtractTimeInfo(DateW[i],"minute")
			string second=ACMCC_ExtractTimeInfo(DateW[i],"second")
		
			ACSM_time_txt[i]=year+"/"+month+"/"+dayofmonth+" "+hour+":"+minute+":"+second
		
		endfor	
	else
		DoAlert/T="WARNING" 0,"Date waves dimension does not match. Please verify."
	endif

End Function