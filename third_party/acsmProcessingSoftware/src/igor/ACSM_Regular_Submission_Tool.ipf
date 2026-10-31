/////////////////////////////////////////////////////////////
//
// Description :
// -------------
//    Generate annual regular ACSM ACTRIS submissions
//
// Copyright (©) 2022:
// -------------------
//     Commissariat à l'énergie atomique et aux énergies alternatives (CEA) ;
//     Centre national de la recherche scientifique (CNRS)
// 
// Author(s) :
// --------
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
//   v1.0.0 : 2022/06/29
//     - first official release
//   v1.0.1 : 2022/07/11
//     - corrected a bug in calling python scripts
//
/////////////////////////////////////////////////////////////




#pragma rtGlobals=1		// Use modern global access method and strict wave access.
#pragma version=4.0
#include <Percentile and Box Plot>

StrConstant ACMCC_Export_version="1.0.1"

///////////////// MENU ////////////////////////////////////////

Menu "ACMCC Annual Submission"
	"Initialize Panel",/q,ACMCC_Initialize_Panel()
End

///////////////// END OF MENU ////////////////////////////////////////

 // This is the function that will be called periodically

Function ACMCC_Initialize_Panel()
	NewDataFolder/O/S root:ACMCC_Export
	Variable/G Number
	String/G ListOfStations="SIRTA;PuydeDome;Barcelona;Athens;Melpitz;Hyytiala;Kosetice;NOA-Athens;Palau Reial;Birkenes;Magurele;Cyprus;Hohenpeissenberg;Lille;Manchester;Bologna;Other"
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
	
	if (datafolderexists("root:acsm_incoming:")==1)
		NextCloud_path=""
		ToF_QuadW[0]="UMR Quad"
		wave DAQ=root:ACSM_Incoming:DAQ_Matrix
		string temp_str
		sprintf temp_str, "%6d",DAQ[0][74]
		SN_str=temp_str
	elseif (datafolderexists("root:Packages:tw_IgorDAQ:")==1)
		NextCloud_path=""
		ToF_QuadW[0]="UMR ToF"
		SN_str=""
	endif
	
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
	FlagList += "111: (V) Irregular data checked and accepted by data originator. Valid measurement;"
	FlagList += "120: (V) Sample reanalysed with similar result;"
	FlagList += "185: (V) Possible local contamination indicated by wind direction or velocity;"
	FlagList += "410: (V) Sahara dust event;"
	FlagList += "420: (V) Preliminary data;"
	FlagList += "456: (I)  	Invalidated by data originator;"
	FlagList += "457: (V) Extremely low value, outside four times standard deviation in a lognormal distribution;"
	FlagList += "458: (V) Extremely high value, outside four times standard deviation in a lognormal distribution;"
	FlagList += "459: (I) Extreme value, unspecified error;"
	FlagList += "460: (I) Contamination suspected;"
	FlagList += "476: (V) Inconsistency discovered through ion balance calculations, but considerd valid;"
	FlagList += "557: (V) Insect contamination, but considered valid;"
	FlagList += "558: (V) Dust contamination, but considered valid;"
	FlagList += "559: (V) Unspecified contamination or local influence, but considered valid;"
	FlagList += "567: (I) Insect contamination, considered invalid;"
	FlagList += "568: (I) Dust contamination, considered invalid;"
	FlagList += "591: (I) Agricultural contamination, considered invalid;"
	FlagList += "593: (I) Industrial contamination, considered invalid;"
	FlagList += "599: (I) Unspecified contamination or local influence ;"
	FlagList += "635: (I) Internal temperatures too far off target value, considered invalid;"
	FlagList += "645: (V) Exceptional traffic nearby;"
	FlagList += "646: (I) Exceptional traffic nearby;"
	FlagList += "647: (V) Fire/wood burning nearby;"
	FlagList += "651: (V) Agricultural activity nearby;"
	FlagList += "652: (V) Construction activity nearby;"
	FlagList += "659: (I) Unspecified instrument/sampling anomaly;"
	FlagList += "660: (V) Unspecified instrument/sampling anomaly;"
	FlagList += "674: (V) Icing or hoar frost in the intake, considered valid;"
	FlagList += "676: (V) station inside cloud (visibility < 1000 m);"
	FlagList += "677: (I) Icing or hoar frost in the intake;"
	FlagList += "678: (V) Hurricane;"
	FlagList += "780: (V) Value below detection or quantification limit, data element contains estimated or measured value;"
	FlagList += "781: (V) Value below detection limit, data element contains detection limit;"
	FlagList += "899: (I) Measurement undefined, unspecified reason;"
	FlagList += "980: (I) Missing due to calibration or zero/span check;"
	FlagList += "999: (I) Missing measurement, unspecified reason;"
	
	Variable/G YearToExport
	
	FindYearToExport()
	
	
//	FlagList += "-1: (?) Other flag - see EBAS website and enter at right;"
	
	ACMCC_Export_Panel()
	
End Function


///////////////// PANEL FUNCTIONS ////////////////////////////////////////

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
	Button CheckCalibButton, title="\\f01Check calib. values", pos={10,230},fSize=14,size={150,25},font="Arial", fcolor=(52224,34816,0), proc=CheckCalibButton_proc
	Button CheckLODButton, title="\\f01Check LOD values", pos={200,230},fSize=14,size={150,25},font="Arial", fcolor=(52224,34816,0), proc=CheckLODButton_proc
	CheckBox UseMiddlebrook_CB, title="Use AN-dependant CE", pos={10,265}, fsize=14,value=ApplyMiddlebrook
	Button GetACSMdataButt, title="\\f01Get ACSM Data & Diagnostics", pos={70,300},fSize=18,size={280,35},font="Arial", fcolor=(52224,34816,0), proc=GetACSM_proc
	
	GroupBox GetErrors,pos={2,350},size={395,80},title="\\f01II/ Errors",fSize=12,fColor=(13056,4352,0),labelBack=(61952,61952,65280),frame=0,font="Arial"
	Button CalcErrorButt, title="\\f01Calculate Errors", pos={10,380},fSize=14,size={150,35},font="Arial", fcolor=(32768,40704,65280), proc=CalcError_proc
	Button CheckErrorButt, title="\\f01Check Error Sanity", pos={200,380},fSize=14,size={150,35},font="Arial", fcolor=(32768,40704,65280), proc=CheckError_proc, disable =2

	GroupBox GetFlags,pos={2,440},size={395,80},title="\\f01III/ Flags",fSize=12,fColor=(13056,4352,0),labelBack=(65280,59648,57600),frame=0,font="Arial"
	Button PreQualifButt, title="\\f01Suggest Flags", pos={10,470},fSize=14,size={150,35},font="Arial", fcolor=(65024,49152,43776), proc=Prequalif_proc
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

Function SetPath_proc(Path_name) : ButtonControl
	String Path_name
	SVAR/Z NextCloud_path=root:ACMCC_Export:NextCloud_path
	
	String temp_folder
	temp_folder = getdatafolder(1)
	
	//define path
	newpath/O/Q path1
	pathinfo path1
	NextCloud_path = S_path
	setdatafolder temp_folder	
	
end Function


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

Function SetPythonPath_proc(Path_name) : ButtonControl
	String Path_name
	SVAR/Z Python_path=root:ACMCC_Export:Python_path
	
	String temp_folder
	temp_folder = getdatafolder(1)
	
	//define path
	newpath/O/Q path1
	pathinfo path1
	Python_path = S_path
	setdatafolder temp_folder


End Function

Function SetPathCS_proc(Path_name) : ButtonControl
	String Path_name
	SVAR/Z PMFInput_path=root:ACMCC_Export:PMFInput_path
	
	String temp_folder
	temp_folder = getdatafolder(1)
	
	//define path
	newpath/O/Q path1
	pathinfo path1
	PMFInput_path = S_path
	setdatafolder temp_folder
end


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


Function SpectroInput_proc(name,num,str) : PopupMenuControl
	string name
	variable num
	string str

	wave/T ToF_QuadW=root:ACMCC_Export:ToF_QuadW
	if(stringmatch(str,"select"))
		DoAlert/T="WARNING" 0,"Please select in the list"
	else
		ToF_QuadW[0]=str
		SVAR/Z NextCloud_path=root:ACMCC_Export:NextCloud_path
		if(stringmatch(str,"UMR ToF"))
			NextCloud_path="C:Users:TofUser:NextCloud:"
		else
			NextCloud_path="C:Users:acsm:Nextcloud:"
		endif
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
		CheckBox UseMiddlebrook_CB, title="Use AN-dependant CE", pos={10,265}, fsize=14,value=ApplyMiddlebrook,disable=2
	elseif(stringmatch(VaporizerW[0],"Standard Vap."))
		ApplyMiddlebrook=1
		CheckBox UseMiddlebrook_CB, title="Use AN-dependant CE", pos={10,265}, fsize=14,value=ApplyMiddlebrook,disable=0
	
		
	endif
	
End Function





///////////////// END OF PANEL FUNCTIONS ////////////////////////////////////////



Function CheckCalibButton_proc(ctrlName) : ButtonControl
	string ctrlName
	SetDataFolder root:ACMCC_Export
	
	//Get IE, RIE and CE values
	Make/N=1/D/O IE_NO3, RIE_NH4, RIE_SO4, RIE_NO3, RIE_OM, RIE_Cl
	wave RIE_W=root:RIE
	RIE_OM=RIE_W[0]
	RIE_NH4=RIE_W[1]
	RIE_SO4=RIE_W[2]
	RIE_NO3=RIE_W[3]
	RIE_Cl=RIE_W[4]
	wave MC_NO3=root:Masscalib_nitrate
	IE_NO3=MC_NO3[0]
	
	edit/K=0 IE_NO3, RIE_OM, RIE_NO3, RIE_NH4, RIE_SO4, RIE_Cl
	
End Function
.
Function CheckLODButton_proc(ctrlName) : ButtonControl
	string ctrlName
	SetDataFolder root:ACMCC_Export
	
	//Get IE, RIE and CE values
	wave ACSMvar,LOD
	
	edit/K=0 ACSMvar,LOD
	
End Function


Function GetACSM_proc(ctrlName) : ButtonControl
	string ctrlName
	NVAR/Z ApplyMiddlebrook=root:ACMCC_Export:ApplyMiddlebrook
	SetDataFolder root:ACMCC_Export
	variable i
	wave DateW=root:ACSM_Incoming:acsm_utc_time
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
	
	Make/N=(numpnts(DateW))/D/O IE_NO3, RIE_NH4, RIE_SO4, RIE_NO3, RIE_OM, RIE_Cl
	wave RIE_W=root:RIE
	RIE_OM=RIE_W[0]
	RIE_NH4=RIE_W[1]
	RIE_SO4=RIE_W[2]
	RIE_NO3=RIE_W[3]
	RIE_Cl=RIE_W[4]
	wave MC_NO3=root:Masscalib_nitrate
	IE_NO3=MC_NO3[0]
	
	
	
	
	Make/O/N=(numpnts(DateW)) CE
	wave CEW=root:CE
	CE=CEW[0]
	
	wave OrgW=root:Time_Series:Org
	wave NO3W=root:Time_Series:NO3
	wave SO4W=root:Time_Series:SO4
	wave NH4W=root:Time_Series:NH4
	wave ClW=root:Time_Series:Chl
	
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
		SO4*=CEW[0]/CE
		NH4*=CEW[0]/CE
		NO3*=CEW[0]/CE
		Cl*=CEW[0]/CE
		OM*=CEW[0]/CE
	endif
	
	
	
	wave RFW=root:diagnostics:RF
	wave ChamberTW=root:diagnostics:ChamberT
	wave AirbeamW=root:diagnostics:Airbeam
	wave NSE=root:diagnostics:NewStart_Events
	wave IPC=root:diagnostics:InletPClosed
	wave IPO=root:diagnostics:InletPOpen
	wave IP=root:diagnostics:InletP
	wave VapTW=root:diagnostics:VapT
	
	duplicate/O RFW RF
	duplicate/O ChamberTW ChamberT
	duplicate/O AirbeamW Airbeam
	duplicate/O NSE NewStart_Events
	duplicate/O IPC InletPClosed
	duplicate/O IPO InletPOpen
	duplicate/O IP InletP
	duplicate/O VapTW VapT
	
	Make/O/N=(numpnts(ACSM_time)) EmCurrent, SEMVol, HeaterBias, VapV
	wave DAQ=root:acsm_incoming:DAQ_Matrix
	EmCurrent[]=DAQ[p][6]
	SEMVol[]=DAQ[p][7]
	HeaterBias[]=5 + DAQ[p][2]*200/5
	VapV[]=DAQ[p][28]
	
	Make/O/N=(numpnts(ACSM_time)) OM_f44, OM_f43, OM_f60, NO3_f30, NO3_f46
	NewDataFolder/S/O root:ACMCC_Export:Temp
	wave OrgMx=root:ACSM_Incoming:OrgStickMatrix
	wave NO3Mx=root:ACSM_Incoming:NO3StickMatrix
	
	ACMCC_DoSumOfRow(OrgMx)
	ACMCC_DoSumOfRow(NO3Mx)
	wave OrgStickMatrix_sum
	wave NO3StickMatrix_sum
	OM_f44=OrgMx[p][44]/OrgStickMatrix_sum[p]
	OM_f43=OrgMx[p][43]/OrgStickMatrix_sum[p]
	OM_f60=OrgMx[p][60]/OrgStickMatrix_sum[p]
	NO3_f30=NO3Mx[p][30]/NO3StickMatrix_sum[p]
	NO3_f46=NO3Mx[p][46]/NO3StickMatrix_sum[p]
	KillDataFolder root:ACMCC_Export:Temp
	SetDataFolder root:ACMCC_Export
	
	//Get general info
	Make/O/N=(numpnts(ACSM_time))/T acsm_local_version
	string temp4=stringfromlist(0, ACMCC_getConst_wrapper("ACMCC_getConst_version_acsm"), " ")
	acsm_local_version=temp4
	Make/O/N=(numpnts(ACSM_time))/T ACMCC_export_ver
	ACMCC_export_ver=ACMCC_Export_version
//	Make/O/N=(numpnts(ACSM_time))/T SerialNumber
//	wave DAQ=root:acsm_incoming:DAQ_Matrix
//	string temp_str
//	sprintf temp_str, "%6d",DAQ[0][74]
//	SerialNumber=temp_str
	
	//Get Pump Diagnostics
	SetDataFolder root:ACMCC_Export	
	Make/O/N=(numpnts(ACSM_time)) TP1_S,TP1_W,TP1_T,TP2_S,TP2_W,TP2_T,TP3_S,TP3_W,TP3_T
	//ACMCC_PumpData()

	//Get Dryer Stats
	SetDataFolder root:ACMCC_Export:
	Make/O/N=(numpnts(ACSM_time)) Sampling_Flowrate, RH_In, RH_Out, T_In, T_Out
	
	Make/O/N=(numpnts(DateW)) numflag_OM
	duplicate/O numflag_OM numflag_NO3,numflag_SO4,numflag_NH4,numflag_Cl
	
	Make/O/N=(numpnts(DateW)) ValidBool_OM=0
	duplicate/O ValidBool_OM ValidBool_NO3,ValidBool_SO4, ValidBool_NH4, ValidBool_Cl
	
	
	Display/K=0 OM,NO3,NH4,SO4,Cl vs ACSM_time
	ModifyGraph lsize=1.5,rgb(OM)=(26112,52224,0),rgb(NO3)=(0,43520,65280);DelayUpdate
	ModifyGraph rgb(NH4)=(65280,43520,0),rgb(SO4)=(52224,0,0);DelayUpdate
	ModifyGraph rgb(Cl)=(65280,32768,58880)
	Label bottom " "

End Function


Function CalcError_proc(ctrlName) : ButtonControl
	string ctrlName
	SetDataFolder root:ACMCC_Export
	wave ACSM_time
	Make/O/N=(numpnts(ACSM_time)) OM_err, NO3_err, SO4_err, NH4_err, Cl_err
	variable i
	
	variable a = 1.2
	string sf = getDatafolder(1); ACMCC_MakeAndOrSetDF( "root:PMFMats" )
	//Get Gain
	variable Gain = 2e4
	variable dwellTMissingFlag = 0
	//Get m/z for electronic noise
	variable DwellTime = 1.2
	variable massForElectronicNoise = 140
	variable electronicNoise = 0
	// Open and closed haven't been RIT (Tm/z) corrected.
	wave OpenMat = root:acsm_incoming:mssopen_mzcorr
	wave ClosedMat = root:acsm_incoming:mssClosed_mzcorr
	wave daq_Matrix = root:acsm_incoming:DAQ_matrix
	wave/Z smCorr_w = root:timeSeries_corrections:smCorr_w
	make/O/N=(dimsize(OpenMat,0)) dwellTW, gainW, eNoiseWave, minErrorW
	variable ACMCC_ka_amu_window=0.05
	dwellTW = 2*ka_amu_window * daq_matrix[p][54] * 0.001*daq_matrix[p][75]
	dwellTW = dwelltW[p] == 0 ? dwellTW[p-1] : dwellTW[p]
	dwellTMissingFlag = 1
	gainW = (gain / smCorr_w[p])*(daq_matrix[p][85]/daq_matrix[p][1])
	eNoiseWave = closedMat[p][massForElectronicNoise]
	wavestats /Q eNoiseWave
		// factors here are to convert to counts...
	eNoiseWave = 6.24e18 * DwellTW[p] * V_Sdev / gainW[p]
	make/O/N=(dimsize(OpenMat,0), dimsize(OpenMat,1)) openMatCts = OpenMat[p][q]*6.24e18*DwellTW[p]/GainW[p]
	make/O/N=(dimsize(ClosedMat,0), dimsize(ClosedMat,1)) ClosedMatCts = ClosedMat[p][q]*6.24e18*DwellTW[p]/GainW[p]
	//Apply RIT Correction to open and closed (in counts)
	MatrixOp/O openMatCts = openMatCts^t
	MatrixOp/O closedMatCts = closedMatCts^t
	MatrixOp/O openMatCts = openMatCts^t
	MatrixOp/O closedMatCts = closedMatCts^t
	//Calculate difference and its error in cts
	MatrixOp/O eOpenMatCts = a*powr(OpenMatCts,0.5)
	MatrixOp/O eClosedMatCts = a*powr(ClosedMatCts,0.5)
	MatrixOp/O openMatCts = openMatCts^t
	MatrixOp/O closedMatCts = closedMatCts^t
	MatrixOp/O eOpenMatCts = eOpenMatCts^t
	MatrixOp/O eClosedMatCts = eClosedMatCts^t
	ACMCC_correctIonTransmission(eOpenMatCts)
	ACMCC_correctIonTransmission(eClosedMatCts)
	ACMCC_correctIonTransmission(openMatCts)
	ACMCC_correctIonTransmission(closedMatCts)
	MatrixOp/O openMatCts = openMatCts^t
	MatrixOp/O closedMatCts = closedMatCts^t
	MatrixOp/O eOpenMatCts = eOpenMatCts^t
	MatrixOp/O eClosedMatCts = eClosedMatCts^t
	MatrixOp/O diffMatCts = OpenMatCts - ClosedMatCts 
	MatrixOp/O eDiffMatCts = powr((powr(eOpenMatCts,2) + powr(eClosedMatCts,2)),0.5)
	//Trim the first column from the matrices (this is a dummy column so p = amu typically)
	deletepoints /M=1 0,1,eDiffMatCts, diffMatCts
	// add electronic Noise
	redimension /N=(dimSize(eDiffMatCts,0), dimSize(eDiffMatCts,1)) eNoiseWave
	enoiseWave = enoiseWave[p][0]
	MatrixOp/O eDiffMatCts = powr((powr(eDiffMatCts,2) + powr(eNoiseWave,2)),0.5)
	//Remove NaNs
	eDiffMatCts = deluxe_Nan2Zero(eDiffMatCts)
	DiffMatCts = deluxe_NaN2Zero(diffMatCts)
	ACMCC_PMF_ReSpeciateWholeTS(DiffMatCts,"Org","Org_Specs")
	ACMCC_PMFErr_ReSpeciateWholeTS(eDiffMatCts,"Org","OrgSpecs_err")
	wave org_specs = root:PMFMats:org_specs
	wave orgSpecs_err = root:PMFMats:orgSpecs_err
	ACMCC_PMFErr_ReSpeciateWholeTS(eDiffMatCts,"NO3","NO3Specs_err")
	wave NO3Specs_err = root:PMFMats:NO3Specs_err
	ACMCC_PMFErr_ReSpeciateWholeTS(eDiffMatCts,"SO4","SO4Specs_err")
	wave SO4Specs_err = root:PMFMats:SO4Specs_err
	ACMCC_PMFErr_ReSpeciateWholeTS(eDiffMatCts,"NH4","NH4Specs_err")
	wave NH4Specs_err = root:PMFMats:NH4Specs_err
	ACMCC_PMFErr_ReSpeciateWholeTS(eDiffMatCts,"Chl","ChlSpecs_err")
	wave ChlSpecs_err = root:PMFMats:ChlSpecs_err
	
	//Convert back to amps
	org_specs *= (GainW[p]/(6.24e18*DwellTW[p]))
	orgSpecs_err *= (GainW[p]/(6.24e18*DwellTW[p]))
	
	NO3Specs_err *= (GainW[p]/(6.24e18*DwellTW[p]))
	
	SO4Specs_err *= (GainW[p]/(6.24e18*DwellTW[p]))
	
	NH4Specs_err *= (GainW[p]/(6.24e18*DwellTW[p]))
	
	ChlSpecs_err *= (GainW[p]/(6.24e18*DwellTW[p]))
	
	// Replace low errors with min error really tiny errors can cause problems in PMF 
	minErrorW = ACMCC_Calc_MinError(GainW,DwellTW)
	orgSpecs_err = ACMCC_Replace_lessThan_withVal(orgSpecs_err[p][q],minErrorW[p],minErrorW[p])
	NO3Specs_err = ACMCC_Replace_lessThan_withVal(NO3Specs_err[p][q],minErrorW[p],minErrorW[p])
	SO4Specs_err = ACMCC_Replace_lessThan_withVal(SO4Specs_err[p][q],minErrorW[p],minErrorW[p])
	NH4Specs_err = ACMCC_Replace_lessThan_withVal(NH4Specs_err[p][q],minErrorW[p],minErrorW[p])
	ChlSpecs_err = ACMCC_Replace_lessThan_withVal(ChlSpecs_err[p][q],minErrorW[p],minErrorW[p])
	
	make /O/N=(dimsize(org_specs,1)) amus = p+1
	
	ACMCC_ApplyCalFactors(org_specs, "org")
	ACMCC_ApplyCalFactors(orgspecs_err, "org")
	ACMCC_ApplyCalFactors(NO3specs_err, "NO3")
	ACMCC_ApplyCalFactors(SO4specs_err, "SO4")
	ACMCC_ApplyCalFactors(NH4specs_err, "NH4")
	ACMCC_ApplyCalFactors(Chlspecs_err, "Chl")
	
	// Pull times wave to keep with the data...UTC! 
	Duplicate /O root:acsm_incoming:acsm_utc_time acsm_utc_time
	Duplicate /O root:acsm_incoming:acsm_local_time acsm_local_time
	//Make flag variables that we'll put up if we've applied downweighting so we don't do it twice!
	NVAR /Z weakDownWeightFlag
	if (!NVAR_Exists(weakDownweightFlag))
		variable /G weakDownweightFlag
	endif	
	weakDownWeightFlag = 0
	NVAR /Z m44relDownWeightFlag
	if (!NVAR_Exists(m44relDownweightFlag))
		variable /G m44relDownweightFlag
	endif
	m44relDownWeightFlag = 0
		NVAR /Z abCorrFlag
	if (!NVAR_Exists(abCorrFlag))
		variable /G abCorrFlag
	endif	
	abCorrFlag = 0
	
	ACMCC_ApplyCorrectionForPMF()
	ACMCC_TrimPMFMats()
	
	MatrixOp/O Org_Specs = Org_Specs^t
	MatrixOp/O Orgspecs_err = Orgspecs_err^t
	MatrixOp/O NO3specs_err = NO3specs_err^t
	MatrixOp/O SO4specs_err = SO4specs_err^t
	MatrixOp/O NH4specs_err = NH4specs_err^t
	MatrixOp/O Chlspecs_err = Chlspecs_err^t
	
	Make/O/N=(numpnts(acsm_utc_time)) eOrg, eNO3, eSO4, eNH4, eChl
	
	string NO3str="13;29;30;31;45;46;47;62"
	string SO4str="15;16;17;18;19;23;31;32;33;47;48;49;51;63;64;65;79;80;81;82;83;84;97;98;99;101"
	string NH4str="14;15;16"
	string Clstr="34;35;36;37"
	
	DeleteRows(NO3specs_err, NO3str)
	DeleteRows(SO4specs_err, SO4str)
	DeleteRows(NH4specs_err, NH4str)
	DeleteRows(Chlspecs_err, Clstr)
	
	MatrixOp/O Org_Specs = Org_Specs^t
	MatrixOp/O Orgspecs_err = Orgspecs_err^t
	MatrixOp/O NO3specs_err = NO3specs_err^t
	MatrixOp/O SO4specs_err = SO4specs_err^t
	MatrixOp/O NH4specs_err = NH4specs_err^t
	MatrixOp/O Chlspecs_err = Chlspecs_err^t
	
//	Extract/O NO3specs_err,NO3specs_err, (p==13 || p==29 || p==30 || p==31 || p==45 || p==46 || p==47 || p==62)
//	Extract/O NH4specs_err,NH4specs_err, (p==14 || p==15 || p==16)
//	Extract/O Chlspecs_err,Chlspecs_err, (p==34 || p==35 || p==36 || p==37)
//	Extract/O SO4specs_err,SO4specs_err, (p==15 || p==16 || p==17 || p==18 || p==19 || p==23 || p==31 || p==32 || p==33 || p==47 || p==48 || p==49 || p==51 || p==63 || p==64 || p==65 || p==79 || p==80 || p==81 || p==82 || p==83 || p==84 || p==97 || p==98 || p==99)
//	
//	
//	eOrg=ACMCC_quadraticSum(Orgspecs_err)
//	eNO3=ACMCC_quadraticSum(NO3specs_err)
//	eSO4=ACMCC_quadraticSum(SO4specs_err)
//	eNH4=ACMCC_quadraticSum(NH4specs_err)
//	eChl=ACMCC_quadraticSum(Chlspecs_err)
//	

	MatrixOp /O NO3specs_err = NO3specs_err*NO3specs_err		
	MatrixOp /O eNO3 = sumRows(NO3specs_err)
	eNO3 = sqrt(eNO3)
	
	MatrixOp /O Orgspecs_err = Orgspecs_err*Orgspecs_err		
	MatrixOp /O eOrg = sumRows(Orgspecs_err)
	eOrg = sqrt(eOrg)
	
	MatrixOp /O SO4specs_err = SO4specs_err*SO4specs_err		
	MatrixOp /O eSO4 = sumRows(SO4specs_err)
	eSO4 = sqrt(eSO4)
	
	MatrixOp /O NH4specs_err = NH4specs_err*NH4specs_err		
	MatrixOp /O eNH4 = sumRows(NH4specs_err)
	eNH4 = sqrt(eNH4)
	
	MatrixOp /O Chlspecs_err = Chlspecs_err*Chlspecs_err		
	MatrixOp /O eChl = sumRows(Chlspecs_err)
	eChl = sqrt(eChl)
	
	OM_err=eOrg
	NO3_err=eNO3
	SO4_err=eSO4
	NH4_err=eNH4
	Cl_err=eChl
	
	SetDataFolder root:ACMCC_Export:
	
	NVAR/Z ApplyMiddlebrook=root:ACMCC_Export:ApplyMiddlebrook
	if(ApplyMiddlebrook==1)
		wave CE
		wave CEW=root:CE
		SO4_err*=CEW[0]/CE
		NH4_err*=CEW[0]/CE
		NO3_err*=CEW[0]/CE
		Cl_err*=CEW[0]/CE
		OM_err*=CEW[0]/CE
	endif
	
	duplicate/O OM_err OM_ferr, NO3_ferr, SO4_ferr,NH4_ferr,Cl_ferr
	wave OM, NO3, SO4, NH4, Cl
	OM_ferr=100*OM_err/OM
	NO3_ferr=100*NO3_err/NO3
	SO4_ferr=100*SO4_err/SO4
	NH4_ferr=100*NH4_err/NH4
	Cl_ferr=100*Cl_err/Cl
	
	fWavePercentile(NameOfWave(OM_ferr), "50", NameOfWave(OM_ferr)+"_p", 0, 0, 0)
	fWavePercentile(NameOfWave(NO3_ferr), "50", NameOfWave(NO3_ferr)+"_p", 0,	0, 0)
	fWavePercentile(NameOfWave(SO4_ferr), "50", NameOfWave(SO4_ferr)+"_p", 0, 0, 0)
	fWavePercentile(NameOfWave(NH4_ferr), "50", NameOfWave(NH4_ferr)+"_p", 0, 	0, 0)
	fWavePercentile(NameOfWave(Cl_ferr), "50", NameOfWave(Cl_ferr)+"_p", 0, 	0, 0)
	
	KillWaves/Z TempSort,TempMatrix,TmpPercentiles, PCNames,OM_ferr_p_N,NO3_ferr_p_N,SO4_ferr_p_N,NH4_ferr_p_N,Cl_ferr_p_N
	wave OM_ferr_p_50,NO3_ferr_p_50,SO4_ferr_p_50,NH4_ferr_p_50,Cl_ferr_p_50
	
	String Result_str="Median errors are: "
	Result_str+="\rOM : "+num2str(OM_ferr_p_50[0]) + " %"
	Result_str+="\rNO3 : "+num2str(NO3_ferr_p_50[0]) + " %"
	Result_str+="\rSO4 : "+num2str(SO4_ferr_p_50[0]) + " %"
	Result_str+="\rNH4 : "+num2str(NH4_ferr_p_50[0]) + " %"
	Result_str+="\rCl : "+num2str(Cl_ferr_p_50[0]) + " %"
	
	print Result_str
	
	
	
	
End Function


Function DeleteRows(waveToUse, listToKeep)
	wave waveToUse
	string listToKeep
	
	variable i, max2use,row
	max2use=dimsize(waveToUse,0)
	
	for(i=0;i<max2use;i+=1)
	//for(i=0;(dimsize(waveToUse,0)-i-1)<0;i+=1)
		//print (dimsize(waveToUse,0)-i-1)
		row=max2use-i-1
		if (findlistitem(num2str(row),listToKeep)==-1)
			deletepoints/M=0 row,1,waveToUse
		endif
	endfor
	
End Function


Function PreQualif_proc(ctrlName) : ButtonControl
	string ctrlName
	SetDataFolder root:ACMCC_Export:
	wave OM, NO3, SO4, NH4,Cl, OM_err,NO3_err,SO4_err,NH4_err,Cl_err,Airbeam, InletP,numflag_OM,numflag_NO3,numflag_SO4,numflag_NH4,numflag_Cl,LOD,VapT
	wave ValidBool_OM,ValidBool_NO3,ValidBool_SO4, ValidBool_NH4, ValidBool_Cl
	wave/T LensW
	variable minInletP,maxInletP
	
	if(stringmatch(LensW[0],"PM1 Lens"))
		minInletP=1.1
		maxInletP=1.5
	elseif(stringmatch(LensW[0],"PM2.5 Lens"))
		minInletP=3.1
		maxInletP=3.6
	endif
	numflag_OM[]=(InletP[p]>maxInletP || InletP[p]<minInletP) ? 659 : numflag_OM[p]
	numflag_NO3[]=(InletP[p]>maxInletP || InletP[p]<minInletP) ? 659 : numflag_NO3[p]
	numflag_SO4[]=(InletP[p]>maxInletP || InletP[p]<minInletP) ? 659 : numflag_SO4[p]
	numflag_NH4[]=(InletP[p]>maxInletP || InletP[p]<minInletP) ? 659 : numflag_NH4[p]
	numflag_Cl[]=(InletP[p]>maxInletP || InletP[p]<minInletP) ? 659 : numflag_Cl[p]
	
	numflag_OM[]=(abs(InletP[p-1]-InletP[p])>0.2) ? 659 : numflag_OM[p]
	numflag_NO3[]=(abs(InletP[p-1]-InletP[p])>0.2) ? 659 : numflag_NO3[p]
	numflag_SO4[]=(abs(InletP[p-1]-InletP[p])>0.2) ? 659 : numflag_SO4[p]
	numflag_NH4[]=(abs(InletP[p-1]-InletP[p])>0.2) ? 659 : numflag_NH4[p]
	numflag_Cl[]=(abs(InletP[p-1]-InletP[p])>0.2) ? 659 : numflag_Cl[p]
	
	numflag_OM[]=(Airbeam[p]<6.0e-8) ? 659 : numflag_OM[p]
	numflag_NO3[]=(Airbeam[p]<6.0e-8) ? 659 : numflag_NO3[p]
	numflag_SO4[]=(Airbeam[p]<6.0e-8) ? 659 : numflag_SO4[p]
	numflag_NH4[]=(Airbeam[p]<6.0e-8) ? 659 : numflag_NH4[p]
	numflag_Cl[]=(Airbeam[p]<6.0e-8) ? 659 : numflag_Cl[p]
	
	numflag_OM[]=(Airbeam[p]>6.0e-8 && Airbeam[p]<8.0e-8 ) ? 660 : numflag_OM[p]
	numflag_NO3[]=(Airbeam[p]>6.0e-8 && Airbeam[p]<8.0e-8 ) ? 660 : numflag_NO3[p]
	numflag_SO4[]=(Airbeam[p]>6.0e-8 && Airbeam[p]<8.0e-8 ) ? 660 : numflag_SO4[p]
	numflag_NH4[]=(Airbeam[p]>6.0e-8 && Airbeam[p]<8.0e-8 ) ? 660 : numflag_NH4[p]
	numflag_Cl[]=(Airbeam[p]>6.0e-8 && Airbeam[p]<8.0e-8 ) ? 660 : numflag_Cl[p]
	
	numflag_OM[]=(VapT[p]>700 || VapT[p]<500 ) ? 660 : numflag_OM[p]
	numflag_NO3[]=(VapT[p]>700 || VapT[p]<500 ) ? 660 : numflag_NO3[p]
	numflag_SO4[]=(VapT[p]>700 || VapT[p]<500 ) ? 660 : numflag_SO4[p]
	numflag_NH4[]=(VapT[p]>700 || VapT[p]<500 ) ? 660 : numflag_NH4[p]
	numflag_Cl[]=(VapT[p]>700 || VapT[p]<500 ) ? 660 : numflag_Cl[p]
	
	numflag_OM[]=(OM[p]<(-3)*LOD[0]) ? 459 : numflag_OM[p]
	numflag_NO3[]=(NO3[p]<(-3)*LOD[1]) ? 459 : numflag_NO3[p]
	numflag_SO4[]=(SO4[p]<(-3)*LOD[2]) ? 459 : numflag_SO4[p]
	numflag_NH4[]=(NH4[p]<(-3)*LOD[3]) ? 459 : numflag_NH4[p]
	numflag_Cl[]=(Cl[p]<(-3)*LOD[4]) ? 459 : numflag_Cl[p]
	
	numflag_OM[]=(abs(OM[p-1]-OM[p])>100) ? 659 : numflag_OM[p]
	numflag_NO3[]=(abs(NO3[p-1]-NO3[p])>100) ? 659 : numflag_NO3[p]
	numflag_SO4[]=(abs(SO4[p-1]-SO4[p])>100) ? 659 : numflag_SO4[p]
	numflag_NH4[]=(abs(NH4[p-1]-NH4[p])>100) ? 659 : numflag_NH4[p]
	numflag_Cl[]=(abs(Cl[p-1]-Cl[p])>100) ? 659 : numflag_Cl[p]
	
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
	
	PopupMenu FlagList_PUM title="\\f01Flag List",pos={10,10},value=FlagItemList(),fsize=18
	PopupMenu Var_PUM title="\\f01Apply on ",pos={10,50},value=VarItemList(),fsize=18
	Button ApplyFlag_Butt, title="\\f01Apply & Update", pos={250,40},fSize=14,size={150,35},font="Arial", fcolor=(43264,58112,43008),proc=ApplyFlag_proc
	CheckBox HideInvalid_CB, title="Hide Invalid", pos={425,50}, fsize=14,proc=HideInvalid_proc


	
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


Function ExportTxt_proc(ctrlName) : ButtonControl
	string ctrlName
	
	variable i
	i=0
	
	SVAR/Z FileName_str=root:ACMCC_Export:FileName_str
	SVAR/Z FlagName_str=root:ACMCC_Export:FlagName_str
	
	SetDataFolder root:ACMCC_Export
	string saveWavesList="ACSM_time_txt;OM;NO3;SO4;NH4;Cl;IE_NO3;RIE_OM;RIE_NO3;RIE_SO4;RIE_NH4;RIE_Cl;"
	saveWavesList+="RF;ChamberT;Airbeam;NewStart_Events;InletPClosed;InletPOpen;InletP;VapT;"
	saveWavesList+="EmCurrent;SEMVol;HeaterBias;VapV;"
	saveWavesList+="OM_f44;OM_f43;OM_f60;NO3_f30;NO3_f46;"
	saveWavesList+="acsm_local_version;ACMCC_export_ver;"
	saveWavesList+="TP1_S;TP1_W;TP1_T;TP2_S;TP2_W;TP2_T;TP3_S;TP3_W;TP3_T;"
	saveWavesList+="Sampling_Flowrate;RH_In;RH_Out;T_In;T_Out;"
	saveWavesList+="OM_err;NO3_err;SO4_err;NH4_err;Cl_err;"
	saveWavesList+="Tof_QuadW;LensW;VaporizerW;"
	
	SetDataFolder root:ACMCC_Export
	wave/T VaporizerW,LensW,ToF_QuadW,StationNameW
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


///////////////// MAIN EXPORT FUNCTIONS ////////////////////////////////////////

Function ACMCC_Quad_TriggeredExport()
	
	SetDataFolder root:ACMCC_Export
	
	//Get IE, RIE and CE values
	Make/N=1/D/O IE_NO3, RIE_NH4, RIE_SO4, RIE_NO3, RIE_OM, RIE_Cl, CE
	wave RIE_W=root:RIE
	RIE_OM=RIE_W[0]
	RIE_NH4=RIE_W[1]
	RIE_SO4=RIE_W[2]
	RIE_NO3=RIE_W[3]
	RIE_Cl=RIE_W[4]
	wave MC_NO3=root:Masscalib_nitrate
	IE_NO3=MC_NO3[0]
	wave CEW=root:CE
	CE=CEW[0]
	
	//Get Date
	Make/N=1/O/T ACSM_time
	wave DateW=root:ACSM_Incoming:acsm_utc_time
	variable lastrow=numpnts(DateW)-1
	
	string year=ACMCC_ExtractDateInfo(DateW[lastrow],"year")
	string month=ACMCC_ExtractDateInfo(DateW[lastrow],"month")
	string dayOfMonth=ACMCC_ExtractDateInfo(DateW[lastrow],"dayOfMonth")
	string hour=ACMCC_ExtractTimeInfo(DateW[lastrow],"hour")
	string minute=ACMCC_ExtractTimeInfo(DateW[lastrow],"minute")
	string second=ACMCC_ExtractTimeInfo(DateW[lastrow],"second")
	
	ACSM_time=year+"/"+month+"/"+dayofmonth+" "+hour+":"+minute+":"+second
	
	//Get Concentrations
	Make/O/N=1 OM,NO3,SO4,NH4,Cl
	wave OrgW=root:Time_Series:Org
	wave NO3W=root:Time_Series:NO3
	wave SO4W=root:Time_Series:SO4
	wave NH4W=root:Time_Series:NH4
	wave ClW=root:Time_Series:Chl
	OM=OrgW[lastrow]
	NO3=NO3W[lastrow]
	SO4=SO4W[lastrow]
	NH4=NH4W[lastrow]
	Cl=ClW[lastrow]
	
	//Get Diagnostics
	Make/O/N=1 RF, ChamberT, Airbeam, NewStart_Events, InletPClosed, InletPOpen, InletP, VapT
	wave RFW=root:diagnostics:RF
	wave ChamberTW=root:diagnostics:ChamberT
	wave AirbeamW=root:diagnostics:Airbeam
	wave NSE=root:diagnostics:NewStart_Events
	wave IPC=root:diagnostics:InletPClosed
	wave IPO=root:diagnostics:InletPOpen
	wave IP=root:diagnostics:InletP
	wave VapTW=root:diagnostics:VapT
	
	RF=RFW[lastrow]
	ChamberT=ChamberTW[lastrow]
	Airbeam=AirbeamW[lastrow]
	NewStart_Events=NSE[lastrow]
	InletPClosed=IPC[lastrow]
	InletPOpen=IPO[lastrow]
	InletP=IP[lastrow]
	VapT=VapTW[lastrow]
	
	//Get Tuning Var
	Make/O/N=1 EmCurrent, SEMVol, HeaterBias, VapV
	wave DAQ=root:acsm_incoming:DAQ_Matrix
	EmCurrent=DAQ[lastrow][6]
	SEMVol=DAQ[lastrow][7]
	HeaterBias=5 + DAQ[lastrow][2]*200/5
	VapV=DAQ[lastrow][28]
	
	//Get f_Org & f_NO3 values
	Make/O/N=1 OM_f44, OM_f43, OM_f60, NO3_f30, NO3_f46
	NewDataFolder/S/O root:ACMCC_Export:Temp
	wave OrgMx=root:ACSM_Incoming:OrgStickMatrix
	wave NO3Mx=root:ACSM_Incoming:NO3StickMatrix
	
	ACMCC_DoSumOfRow(OrgMx)
	ACMCC_DoSumOfRow(NO3Mx)
	wave OrgStickMatrix_sum
	wave NO3StickMatrix_sum
	OM_f44=OrgMx[lastrow][44]/OrgStickMatrix_sum[lastrow]
	OM_f43=OrgMx[lastrow][43]/OrgStickMatrix_sum[lastrow]
	OM_f60=OrgMx[lastrow][60]/OrgStickMatrix_sum[lastrow]
	NO3_f30=NO3Mx[lastrow][30]/NO3StickMatrix_sum[lastrow]
	NO3_f46=NO3Mx[lastrow][46]/NO3StickMatrix_sum[lastrow]
	KillDataFolder root:ACMCC_Export:Temp
	SetDataFolder root:ACMCC_Export

	//Get general info
	Make/O/N=1/T acsm_local_version
	
	//acsm_local_version=versionStr
	acsm_local_version=stringfromlist(0, ACMCC_getConst_wrapper("ACMCC_getConst_version_acsm"), " ")
	//acsm_local_version=""
	Make/O/N=1/T ACMCC_export_ver
	ACMCC_export_ver=ACMCC_Export_version
	Make/O/N=1/T SerialNumber
	wave DAQ=root:acsm_incoming:DAQ_Matrix
	string temp_str
	sprintf temp_str, "%6d",DAQ[lastrow][74]
	SerialNumber=temp_str
	
	//Get Pump Diagnostics
	SetDataFolder root:ACMCC_Export	
	Make/O/N=1 TP1_S,TP1_W,TP1_T,TP2_S,TP2_W,TP2_T,TP3_S,TP3_W,TP3_T
	//ACMCC_PumpData()

	//Get Dryer Stats
	SetDataFolder root:ACMCC_Export:
	Make/O/N=1 Sampling_Flowrate, RH_In, RH_Out, T_In, T_Out
	ACMCC_DryerStat_avg(lastrow)
	wave FlowR_avg=root:DryerData:FlowR_avg
	wave T_In_avg=root:DryerData:T_In_avg
	wave T_Out_avg=root:DryerData:T_Out_avg
	wave RH_In_avg=root:DryerData:RH_In_avg
	wave RH_Out_avg=root:DryerData:RH_Out_avg
	Sampling_Flowrate=FlowR_avg[0]
	T_In=T_In_avg[0]
	T_Out=T_Out_avg[0]
	RH_In=RH_In_avg[0]
	RH_Out=RH_Out_avg[0]
	
	//Get Concentration Errors
	SetDataFolder root:ACMCC_Export	
	Make/O/N=1 OM_err, NO3_err, SO4_err, NH4_err, Cl_err
	ACMCC_Quad_Error(lastrow)
	wave eChl=root:PMFMats:eChl
	wave eOrg=root:PMFMats:eOrg
	wave eSO4=root:PMFMats:eSO4
	wave eNO3=root:PMFMats:eNO3
	wave eNH4=root:PMFMats:eNH4
	OM_err=eOrg
	NO3_err=eNO3
	SO4_err=eSO4
	NH4_err=eNH4
	Cl_err=eChl
	
	//Create Table & Save
	variable i
	i=0
	
	SetDataFolder root:ACMCC_Export
	string saveWavesList="ACSM_time;OM;NO3;SO4;NH4;Cl;IE_NO3;RIE_OM;RIE_NO3;RIE_SO4;RIE_NH4;RIE_Cl;"
	saveWavesList+="RF;ChamberT;Airbeam;NewStart_Events;InletPClosed;InletPOpen;InletP;VapT;"
	saveWavesList+="EmCurrent;SEMVol;HeaterBias;VapV;"
	saveWavesList+="OM_f44;OM_f43;OM_f60;NO3_f30;NO3_f46;"
	saveWavesList+="acsm_local_version;ACMCC_export_ver;"
	saveWavesList+="TP1_S;TP1_W;TP1_T;TP2_S;TP2_W;TP2_T;TP3_S;TP3_W;TP3_T;"
	saveWavesList+="Sampling_Flowrate;RH_In;RH_Out;T_In;T_Out;"
	saveWavesList+="OM_err;NO3_err;SO4_err;NH4_err;Cl_err;"
	saveWavesList+="Tof_QuadW;LensW;VaporizerW;"
	
	SetDataFolder root:ACMCC_Export
	wave/T VaporizerW,LensW,ToF_QuadW
	for (i=0;i<itemsInList(saveWavesList);i+=1)
		wave w = $stringFromList(i,saveWavesList)
		if (i==0)
			Edit /N=ExportTable w
		else
			AppendToTable /W=ExportTable w
		endif
	endfor
	
	SetDataFolder root:ACMCC_Export
	Wave/T SerialNumber
	Wave/T StationNameW
	
	string FileName=StationNameW[0]+"_ACSM-"+SerialNumber[0]+"_"
	FileName+=year+month+dayofmonth+hour+minute+".txt"
	
	SVAR/Z NextCloud_path=root:ACMCC_Export:NextCloud_path
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
	saveTableCopy/O/T=1/W=ExportTable/P=SaveDataFilePathbis as FileName
	KillWindow ExportTable
	
	NVAR/Z GeneratePMFInput=root:ACMCC_Export:GeneratePMFInput
	if (GeneratePMFInput==1)
		SetDataFolder root:PMFMats:
		wave Org_Specs,Orgspecs_err,amus
				
		Edit/N=PMFExportTable ACSM_time
		AppendToTable /W=PMFExportTable amus
		AppendToTable /W=PMFExportTable Orgspecs_err
		AppendToTable /W=PMFExportTable Org_Specs
		ModifyTable/W=PMFExportTable format(ACSM_time)=8
		
		FileName=StationNameW[0]+"_ACSM-"+SerialNumber[0]+"_"+"PMF_"+year+month+dayofmonth+hour+minute+".txt"
		saveTableCopy/O/T=1/W=PMFExportTable/P=SaveDataFilePathbis as FileName
		KillWindow PMFExportTable
	endif
End Function


Function ACMCC_ToF_TriggeredExport()
	
	SetDataFolder root:ACMCC_Export
	
	//Get Date
	Make/N=1/O/T ACSM_time
	NVAR lastrow=root:ACMCC_Export:Number
	wave DateW=root:Packages:tw_IgorDAQ:ACSM:nativeTS:t_stop
	//variable lastrow=numpnts(DateW)-1
	
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
	//wave CEW=root:CE
	//CE=CEW[0]
	
	
	
	//Get Concentrations
	Make/O/N=1 OM,NO3,SO4,NH4,Cl
	OM=DataW[lastrow][7]
	NO3=DataW[lastrow][6]
	SO4=DataW[lastrow][8]
	NH4=DataW[lastrow][5]
	Cl=DataW[lastrow][4]
	
	//Get Diagnostics
//	Make/O/N=1 RF, ChamberT, Airbeam, NewStart_Events, InletPClosed, InletPOpen, InletP, VapT
//	wave RFW=root:diagnostics:RF
//	wave ChamberTW=root:diagnostics:ChamberT
//	wave AirbeamW=root:diagnostics:Airbeam
//	wave NSE=root:diagnostics:NewStart_Events
//	wave IPC=root:diagnostics:InletPClosed
//	wave IPO=root:diagnostics:InletPOpen
//	wave IP=root:diagnostics:InletP
//	wave VapTW=root:diagnostics:VapT
//	
//	RF=RFW[lastrow]
//	ChamberT=ChamberTW[lastrow]
//	Airbeam=AirbeamW[lastrow]
//	NewStart_Events=NSE[lastrow]
//	InletPClosed=IPC[lastrow]
//	InletPOpen=IPO[lastrow]
//	InletP=IP[lastrow]
//	VapT=VapTW[lastrow]
	
	//Get Tuning Var
//	Make/O/N=1 EmCurrent, SEMVol, HeaterBias, VapV
//	wave DAQ=root:acsm_incoming:DAQ_Matrix
//	EmCurrent=DAQ[lastrow][6]
//	SEMVol=DAQ[lastrow][7]
//	HeaterBias=5 + DAQ[lastrow][2]*200/5
//	VapV=DAQ[lastrow][28]
	
	//Get f_Org & f_NO3 values
//	Make/O/N=1 OM_f44, OM_f43, OM_f60, NO3_f30, NO3_f46
//	NewDataFolder/S/O root:ACMCC_Export:Temp
//	wave OrgMx=root:ACSM_Incoming:OrgStickMatrix
//	wave NO3Mx=root:ACSM_Incoming:NO3StickMatrix
//	
//	ACMCC_DoSumOfRow(OrgMx)
//	ACMCC_DoSumOfRow(NO3Mx)
//	wave OrgStickMatrix_sum
//	wave NO3StickMatrix_sum
//	OM_f44=OrgMx[lastrow][44]/OrgStickMatrix_sum[lastrow]
//	OM_f43=OrgMx[lastrow][43]/OrgStickMatrix_sum[lastrow]
//	OM_f60=OrgMx[lastrow][60]/OrgStickMatrix_sum[lastrow]
//	NO3_f30=NO3Mx[lastrow][30]/NO3StickMatrix_sum[lastrow]
//	NO3_f46=NO3Mx[lastrow][46]/NO3StickMatrix_sum[lastrow]
//	KillDataFolder root:ACMCC_Export:Temp
//	SetDataFolder root:ACMCC_Export

	//Get general info
//	Make/O/N=1/T acsm_local_version
	//acsm_local_version=versionStr
	Make/O/N=1/T ACMCC_export_ver
	ACMCC_export_ver=ACMCC_Export_version
	Make/O/N=1/T SerialNumber
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
	SetDataFolder root:ACMCC_Export	
	Make/O/N=1 OM_err,NO3_err,SO4_err,NH4_err,Cl_err
	//duplicate/O eOrg, OM_err
	//duplicate/O eNO3, NO3_err
	//duplicate/O eSO4, SO4_err
	//duplicate/O eNH4, NH4_err
	//duplicate/O eChl, Cl_err
	
	//Create Table & Save
	variable i
	i=0
	string saveWavesList="ACSM_time;OM;NO3;SO4;NH4;Cl;IE_NO3;RIE_OM;RIE_NO3;RIE_SO4;RIE_NH4;RIE_Cl;"
//	saveWavesList+="RF;ChamberT;Airbeam;NewStart_Events;InletPClosed;InletPOpen;InletP;VapT;"
//	saveWavesList+="EmCurrent;SEMVol;HeaterBias;VapV;"
//	saveWavesList+="OM_f44;OM_f43;OM_f60;NO3_f30;NO3_f46;"
	saveWavesList+="ACMCC_export_ver;"
//	saveWavesList+="TP1_S;TP1_W;TP1_T;TP2_S;TP2_W;TP2_T;TP3_S;TP3_W;TP3_T;"
//	saveWavesList+="Sampling_Flowrate;RH_In;RH_Out;T_In;T_Out;"
	saveWavesList+="OM_err;NO3_err;SO4_err;NH4_err;Cl_err;"
	
	
	SetDataFolder root:ACMCC_Export
	for (i=0;i<itemsInList(saveWavesList);i+=1)
		wave w = $stringFromList(i,saveWavesList)
		if (i==0)
			Edit /N=ExportTable w
		else
			AppendToTable /W=ExportTable w
		endif
	endfor
	
	SetDataFolder root:ACMCC_Export
	Wave/T SerialNumber
	Wave/T StationNameW
	
	string FileName=StationNameW[0]+"_ACSM-"+SerialNumber[0]+"_"
	FileName+=year+month+dayofmonth+hour+minute+".txt"
	
	SVAR/Z NextCloud_path=root:ACMCC_Export:NextCloud_path
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
	
End Function


/////////////////END OF MAIN EXPORT FUNCTIONS ////////////////////////////////////////


/////////////////ERROR FUNCTIONS ////////////////////////////////////////

Function ACMCC_Quad_Error(lastrow)
	variable lastrow

	variable a = 1.2
	string sf = getDatafolder(1); ACMCC_MakeAndOrSetDF( "root:PMFMats" )
	//Get Gain
	variable Gain = 2e4
	variable dwellTMissingFlag = 0
	//Get m/z for electronic noise
	variable DwellTime = 1.2
	variable massForElectronicNoise = 140
	variable electronicNoise = 0
	// Open and closed haven't been RIT (Tm/z) corrected.
	wave OpenMat = root:acsm_incoming:mssopen_mzcorr
	wave ClosedMat = root:acsm_incoming:mssClosed_mzcorr
	wave daq_Matrix = root:acsm_incoming:DAQ_matrix
	wave/Z smCorr_w = root:timeSeries_corrections:smCorr_w
	
	Make/O/N=(1,dimsize(OpenMat,1)) OpenMat_LR,ClosedMat_LR,daq_Matrix_LR
	OpenMat_LR[0][]=OpenMat[lastrow][q]
	ClosedMat_LR[0][]=ClosedMat[lastrow][q]
	daq_Matrix_LR[0][]=daq_Matrix_LR[lastrow][q]
	
	make/O/N=1 dwellTW, gainW, eNoiseWave, minErrorW
	make/O/N=(dimsize(OpenMat,0)) eNoiseWave_temp
	variable ACMCC_ka_amu_window=0.05
	dwellTW = 2*ACMCC_ka_amu_window * daq_matrix[lastrow][54] * 0.001*daq_matrix[lastrow][75]
	dwellTMissingFlag = 1
	gainW = (gain / smCorr_w[lastrow])*(daq_matrix[lastrow][85]/daq_matrix[lastrow][1])
	
	// calculate electronic noise based on closed data for a m/z with no real signal
	if (massForElectronicNoise != 0)
		 eNoiseWave_temp = closedMat[p][massForElectronicNoise]
		wavestats /Q  eNoiseWave_temp
		// factors here are to convert to counts...
		eNoiseWave = 6.24e18 * DwellTW[0] * V_Sdev / gainW[0]
	endif
	
	
	make/O/N=(1, dimsize(OpenMat,1)) openMatCts = OpenMat[lastrow][q]*6.24e18*DwellTW[0]/GainW[0]
	make/O/N=(1, dimsize(ClosedMat,1)) ClosedMatCts = ClosedMat[lastrow][q]*6.24e18*DwellTW[0]/GainW[0]
	
	//Apply RIT Correction to open and closed (in counts)
	MatrixOp/O openMatCts = openMatCts^t
	MatrixOp/O closedMatCts = closedMatCts^t
	//These were commented out for V1.5.3.5 b/c it reverts to default
	//ACSM_correctIonTransmission(openMatCts)
	//ACSM_correctIonTransmission(closedMatCts)
	// Move these in 1.5.14.0 to after calculating the counting error per comment from Jay Slowik.
	//ACSM_PMF_correctIonTransmission(openMatCts)
	//ACSM_PMF_correctIonTransmission(closedMatCts)
	MatrixOp/O openMatCts = openMatCts^t
	MatrixOp/O closedMatCts = closedMatCts^t
	//Calculate difference and its error in cts
	MatrixOp/O eOpenMatCts = a*powr(OpenMatCts,0.5)
	MatrixOp/O eClosedMatCts = a*powr(ClosedMatCts,0.5)
	MatrixOp/O openMatCts = openMatCts^t
	MatrixOp/O closedMatCts = closedMatCts^t
	MatrixOp/O eOpenMatCts = eOpenMatCts^t
	MatrixOp/O eClosedMatCts = eClosedMatCts^t
	ACMCC_correctIonTransmission(eOpenMatCts)
	ACMCC_correctIonTransmission(eClosedMatCts)
	ACMCC_correctIonTransmission(openMatCts)
	ACMCC_correctIonTransmission(closedMatCts)
	MatrixOp/O openMatCts = openMatCts^t
	MatrixOp/O closedMatCts = closedMatCts^t
	MatrixOp/O eOpenMatCts = eOpenMatCts^t
	MatrixOp/O eClosedMatCts = eClosedMatCts^t
	MatrixOp/O diffMatCts = OpenMatCts - ClosedMatCts 
	MatrixOp/O eDiffMatCts = powr((powr(eOpenMatCts,2) + powr(eClosedMatCts,2)),0.5)
	//Trim the first column from the matrices (this is a dummy column so p = amu typically)
	deletepoints /M=1 0,1,eDiffMatCts, diffMatCts
	// add electronic Noise
	redimension /N=(dimSize(eDiffMatCts,0), dimSize(eDiffMatCts,1)) eNoiseWave
	enoiseWave = enoiseWave[p][0]
	MatrixOp/O eDiffMatCts = powr((powr(eDiffMatCts,2) + powr(eNoiseWave,2)),0.5)
	//Remove NaNs
	eDiffMatCts = ACMCC_Deluxe_nan2zero(eDiffMatCts)
	DiffMatCts = ACMCC_Deluxe_nan2zero(diffMatCts)
	// These guys push the data through the matrix math
	ACMCC_PMF_ReSpeciateWholeTS(DiffMatCts,"Org","Org_Specs")
	ACMCC_PMFErr_ReSpeciateWholeTS(eDiffMatCts,"Org","OrgSpecs_err")
	wave org_specs = root:PMFMats:org_specs
	wave orgSpecs_err = root:PMFMats:orgSpecs_err
	ACMCC_PMFErr_ReSpeciateWholeTS(eDiffMatCts,"NO3","NO3Specs_err")
	wave NO3Specs_err = root:PMFMats:NO3Specs_err
	ACMCC_PMFErr_ReSpeciateWholeTS(eDiffMatCts,"SO4","SO4Specs_err")
	wave SO4Specs_err = root:PMFMats:SO4Specs_err
	ACMCC_PMFErr_ReSpeciateWholeTS(eDiffMatCts,"NH4","NH4Specs_err")
	wave NH4Specs_err = root:PMFMats:NH4Specs_err
	ACMCC_PMFErr_ReSpeciateWholeTS(eDiffMatCts,"Chl","ChlSpecs_err")
	wave ChlSpecs_err = root:PMFMats:ChlSpecs_err
	
	//Convert back to amps
	org_specs *= (GainW[0]/(6.24e18*DwellTW[0]))
	orgSpecs_err *= (GainW[0]/(6.24e18*DwellTW[0]))
	
	NO3Specs_err *= (GainW[0]/(6.24e18*DwellTW[0]))
	
	SO4Specs_err *= (GainW[0]/(6.24e18*DwellTW[0]))
	
	NH4Specs_err *= (GainW[0]/(6.24e18*DwellTW[0]))
	
	ChlSpecs_err *= (GainW[0]/(6.24e18*DwellTW[0]))
	
	// Replace low errors with min error really tiny errors can cause problems in PMF 
	minErrorW = ACMCC_Calc_MinError(GainW,DwellTW)
	orgSpecs_err = ACMCC_Replace_lessThan_withVal(orgSpecs_err[p][q],minErrorW[p],minErrorW[p])
	NO3Specs_err = ACMCC_Replace_lessThan_withVal(NO3Specs_err[p][q],minErrorW[p],minErrorW[p])
	SO4Specs_err = ACMCC_Replace_lessThan_withVal(SO4Specs_err[p][q],minErrorW[p],minErrorW[p])
	NH4Specs_err = ACMCC_Replace_lessThan_withVal(NH4Specs_err[p][q],minErrorW[p],minErrorW[p])
	ChlSpecs_err = ACMCC_Replace_lessThan_withVal(ChlSpecs_err[p][q],minErrorW[p],minErrorW[p])
	
	// Create an AMU wave
	make /O/N=(dimsize(org_specs,1)) amus = p+1
	// Convert data and error to ug/m3
	ACMCC_ApplyCalFactors(org_specs, "org")
	ACMCC_ApplyCalFactors(orgspecs_err, "org")
	ACMCC_ApplyCalFactors(NO3specs_err, "NO3")
	ACMCC_ApplyCalFactors(SO4specs_err, "SO4")
	ACMCC_ApplyCalFactors(NH4specs_err, "NH4")
	ACMCC_ApplyCalFactors(Chlspecs_err, "Chl")
	
	// Pull times wave to keep with the data...UTC! 
	Duplicate /O root:acsm_incoming:acsm_utc_time acsm_utc_time
	Duplicate /O root:acsm_incoming:acsm_local_time acsm_local_time
	//Make flag variables that we'll put up if we've applied downweighting so we don't do it twice!
	NVAR /Z weakDownWeightFlag
	if (!NVAR_Exists(weakDownweightFlag))
		variable /G weakDownweightFlag
	endif	
	weakDownWeightFlag = 0
	NVAR /Z m44relDownWeightFlag
	if (!NVAR_Exists(m44relDownweightFlag))
		variable /G m44relDownweightFlag
	endif
	m44relDownWeightFlag = 0
		NVAR /Z abCorrFlag
	if (!NVAR_Exists(abCorrFlag))
		variable /G abCorrFlag
	endif	
	abCorrFlag = 0
	// Find columns that are zero and remove them 
	// Remove m/z 19 and 20 since they are small and calculated from 44 (would require more downweighting to keep them)
	//remove_zero_columns_19and20()
	
	ACMCC_ApplyCorrectionForPMF()
	ACMCC_TrimPMFMats()
	
	MatrixOp/O Org_Specs = Org_Specs^t
	MatrixOp/O Orgspecs_err = Orgspecs_err^t
	MatrixOp/O NO3specs_err = NO3specs_err^t
	MatrixOp/O SO4specs_err = SO4specs_err^t
	MatrixOp/O NH4specs_err = NH4specs_err^t
	MatrixOp/O Chlspecs_err = Chlspecs_err^t
	
	Make/O/N=1 eOrg, eNO3, eSO4, eNH4, eChl
	
	string NO3str="13;29;30;31;45;46;47;62"
	string SO4str="15;16;17;18;19;23;31;32;33;47;48;49;51;63;64;65;79;80;81;82;83;84;97;98;99;101"
	string NH4str="14;15;16"
	string Clstr="34;35;36;37"
	
	Extract/O NO3specs_err,NO3specs_err, (p==13 || p==29 || p==30 || p==31 || p==45 || p==46 || p==47 || p==62)
	Extract/O NH4specs_err,NH4specs_err, (p==14 || p==15 || p==16)
	Extract/O Chlspecs_err,Chlspecs_err, (p==34 || p==35 || p==36 || p==37)
	Extract/O SO4specs_err,SO4specs_err, (p==15 || p==16 || p==17 || p==18 || p==19 || p==23 || p==31 || p==32 || p==33 || p==47 || p==48 || p==49 || p==51 || p==63 || p==64 || p==65 || p==79 || p==80 || p==81 || p==82 || p==83 || p==84 || p==97 || p==98 || p==99)
	
	
	eOrg=ACMCC_quadraticSum(Orgspecs_err)
	eNO3=ACMCC_quadraticSum(NO3specs_err)
	eSO4=ACMCC_quadraticSum(SO4specs_err)
	eNH4=ACMCC_quadraticSum(NH4specs_err)
	eChl=ACMCC_quadraticSum(Chlspecs_err)

End Function


Function ACMCC_Calc_MinError(gain, dwell_time)
variable gain
variable dwell_time
	variable a = 1.2
	variable error
	variable EperS = 6.24e18
	error = a * sqrt(2)*gain/(dwell_time*EperS)
return error
End

Function ACMCC_Deluxe_nan2zero(num)
//& Returns the number is real, 0 if not
    variable num
    return numtype(num)!=0?(0):(num)
End

Function ACMCC_ApplyCalFactors(waveToScale, speciesStr)
wave waveToScale
string speciesStr
if (numpnts(waveToScale) > 1)
	wave/T specNames = root:specname
	wave RIE = root:RIE
	wave CE = root:CE
	wave MassCalib_nitrate = root:massCalib_nitrate
	variable i, scalingFactor
	for (i=0; i< numpnts(RIE); i+=1)
		if (stringmatch(speciesStr, specNames[i]))
			scalingFactor = 1/(CE[i]*RIE[i]*massCalib_nitrate[0])
		endif	
	endfor	
	waveToScale *= scalingFactor
endif
End		


Function ACMCC_Replace_lessThan_withVal(num, val, lessThanVal)
variable num
variable val
variable lessThanVal
	return num < lessThanVal?(val):(num)
End


Function ACMCC_correctIonTransmission(msMat)
	Wave msMat
	string sf=getDataFolder(1)
	string ACMCC_ksa_ACSMPanelName="ACSM_ControlWindow"
	ControlInfo/W=$ACMCC_ksa_ACSMPanelName	an_RIT_Corr_ck
	switch(V_Value)
		case 0:
			wave itc = root:acsm:ion_transmission_correction
			break
		case 1:
			wave itc = root:RIT:averageRITFit
			break
	endswitch			
	msMat	/= itc(x)	
	setDataFolder $sf
End



Function ACMCC_PMF_ReSpeciateWholeTS(diffMat, specName, destStr)
wave diffMat
string SpecName,destStr
	string fragMatStr = "root:ms_mats:" + specName + "_mat"
	wave FragMat = $fragMatStr
	duplicate /O diffMat diffMatno1s
	// trim matrices to same amus as data and turn everything in the right direction
	variable amus = dimsize(diffMatNo1s,1)
	make /O/N=(amus,amus) tempFragMat = fragMat[p][q]
	matrixOp /O tempFragMat = tempFragMat^t
	MatrixOp /O tempDiffMat = diffMatNo1s^t
	// Do the multiplication then flip around again
	MatrixOp /O result = tempFragMat x tempDiffMat
	MatrixOp /O result = result^t
	// put the result where we want to
	duplicate /O result $destStr
	// kill the stuff we don't need
	killWaves tempFragMat, tempDiffMat, result
End


Function ACMCC_PMFErr_ReSpeciateWholeTS(diffMat, specName, destStr)
wave diffMat
string SpecName,destStr
	string fragMatStr = "root:ms_mats:" + specName + "_mat"
	wave FragMat = $fragMatStr
	duplicate /O diffMat diffMatno1s
	// trim matrices to same amus as data and turn everything in the right direction
	variable amus = dimsize(diffMatNo1s,1)
	make /O/N=(amus,amus) tempFragMat = fragMat[p][q]
	matrixOp /O tempFragMat = tempFragMat^t
	MatrixOp /O tempDiffMat = diffMatNo1s^t
	// Do the multiplication then flip around again
	MatrixOp/O tempFragMat = powr(tempFragMat,2)
	MatrixOp/O tempDiffMat = powr(tempDiffMat,2)
	MatrixOp /O result = tempFragMat x tempDiffMat
	MatrixOp /O result = result^t
	MatrixOp/O result = powr(result,0.5)
	// put the result where we want to
	duplicate /O result $destStr
	// kill the stuff we don't need
	killWaves tempFragMat, tempDiffMat, result
End



Function ACMCC_ApplyCorrectionForPMF()

	NVAR abCorrFlag = root:PMFMats:abCorrFlag


	wave org_specs = root:pmfmats:org_specs
	wave orgSpecs_err = root:pmfmats:orgSpecs_err
	//wave NO3_specs = root:pmfmats:NO3_specs
	wave NO3Specs_err = root:pmfmats:NO3Specs_err
	//wave SO4_specs = root:pmfmats:SO4_specs
	wave SO4Specs_err = root:pmfmats:SO4Specs_err
	//wave NH4_specs = root:pmfmats:NH4_specs
	wave NH4Specs_err = root:pmfmats:NH4Specs_err
	//wave Chl_specs = root:pmfmats:Chl_specs
	wave ChlSpecs_err = root:pmfmats:ChlSpecs_err
	
	
	
	wave/Z corrW = root:TimeSeries_corrections:smCorr_w
	duplicate /O corrW root:PMFMats:corrW

	org_specs[][] *= corrW[p]
	orgSpecs_err[][] *= corrW[p]
	//NO3_specs[][] *= corrW[p]
	NO3Specs_err[][] *= corrW[p]
	//SO4_specs[][] *= corrW[p]
	SO4Specs_err[][] *= corrW[p]
	//NH4_specs[][] *= corrW[p]
	NH4Specs_err[][] *= corrW[p]
	//Chl_specs[][] *= corrW[p]
	ChlSpecs_err[][] *= corrW[p]

end


Function ACMCC_TrimPMFMats()
	wave amus = root:pmfmats:amus
	variable maxAMU=100
	wave org_specs = root:pmfmats:org_specs
	wave orgSpecs_err = root:pmfmats:orgSpecs_err
	//wave NO3_specs = root:pmfmats:NO3_specs
	wave NO3Specs_err = root:pmfmats:NO3Specs_err
	//wave SO4_specs = root:pmfmats:SO4_specs
	wave SO4Specs_err = root:pmfmats:SO4Specs_err
	//wave NH4_specs = root:pmfmats:NH4_specs
	wave NH4Specs_err = root:pmfmats:NH4Specs_err
	//wave Chl_specs = root:pmfmats:Chl_specs
	wave ChlSpecs_err = root:pmfmats:ChlSpecs_err
	variable pt = binarySearch(amus, maxAMU)
	variable n = numPnts(amus)
	deletepoints pt+1, n-pt, amus
	deletePoints /M=1 pt+1, n-pt, org_specs, orgSpecs_err ,NO3Specs_err,SO4Specs_err,NH4Specs_err,ChlSpecs_err
	
End


Function ACMCC_quadraticSum(wavetosum)
	wave wavetosum
	duplicate/O wavetosum temp
	temp*=temp
	return sqrt(sum(temp))
	killwaves/z temp
end function


Function ACMCC_ToF_Error()



End Function

/////////////////END OF ERROR FUNCTIONS ////////////////////////////////////////


Function ACMCC_DoSumOfRow(mx)
	wave mx
	variable i,j,nbrows,nbcols
	nbrows=dimsize(mx,0)
	nbcols=dimsize(mx,1)
	Make/O/N=(nbrows) $(Nameofwave(mx)+"_sum")
	wave rowSums=$(Nameofwave(mx)+"_sum")
	for (i=0;i<nbrows;i+=1)
		for(j=1;j<nbcols;j+=1)
			rowSums[i]+=mx[i][j]
		endfor
	endfor
End Function

Function ACMCC_PumpData()
	
	string PumpDataFileName="PumpData.txt"
	string PumpDataFilePath="C:ACSM:PumpData:"
	
	wave TP1_S,TP1_W,TP1_T,TP2_S,TP2_W,TP2_T,TP3_S,TP3_W,TP3_T

	
	GetFileFolderInfo/Q/Z=1  (PumpDataFilePath + PumpDataFileName)
	
	NewDataFolder/O/S root:ACMCC_Export:PumpData
	
	if (V_flag==0 && V_isfile)
	
		NewPath/Q/O filePath, PumpDataFilePath
		LoadWave /A/J/P=filePath/W/L={0,1,0,0,16}/K=1/O/Q PumpDataFileName
		killPath filePath
		// get rid of any NaNs caused by newStarts writing header lines
		string waveListStr = waveList("*",";","")
		variable i,j
		string wName = stringFromList(0,waveListStr)
		wave w = $wName
		for (i=0; i<numpnts(w); i+=1)
			if (numType(w[i]) == 2)
				for (j=0;j<itemsInList(wavelistStr); j+=1)
					string wName2 = stringfromList(j,wavelistStr) 
					wave ww = $wName2
					deletepoints i,1,ww
				endfor
				i-=1
			endif
		endfor
		
		SetDataFolder root:ACSM_Incoming
		wave acsm_utc_time
		duplicate/O acsm_local_time, root:ACMCC_Export:PumpData:timeline
		SetDataFolder root:ACMCC_Export:PumpData
		wave timeline,P_DateTime,P1_S,P1_W,P1_T,P2_S,P2_W,P2_T,P3_S,P3_W,P3_T
	
		ACMCC_Avg_WaveList(P_DateTime,"P1_S;P1_W;P1_T;P2_S;P2_W;P2_T;P3_S;P3_W;P3_T",timeline)
		wave P1_S_avg,P1_W_avg,P1_T_avg,P2_S_avg,P2_W_avg,P2_T_avg,P3_S_avg,P3_W_avg,P3_T_avg
		
		TP1_S=P1_S_avg[-2]
		TP1_W=P1_W_avg[-2]
		TP1_T=P1_T_avg[-2]
		TP2_S=P2_S_avg[-2]
		TP2_W=P2_W_avg[-2]
		TP2_T=P2_T_avg[-2]
		TP3_S=P3_S_avg[-2]
		TP3_W=P3_W_avg[-2]
		TP3_T=P3_T_avg[-2]
		
		
	else
		print "Pump DataFile not found"
		TP1_S=-999
		TP1_W=-999
		TP1_T=-999
		TP2_S=-999
		TP2_W=-999
		TP2_T=-999
		TP3_S=-999
		TP3_W=-999
		TP3_T=-999	
	endif
	
End


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



Function ACMCC_Determinehour(dt)
	Variable dt					// Input date/time value
	Variable time = mod(dt, 24*60*60)	// Get the time component of the date/time
	return trunc(time/(60*60))
End




Function ACMCC_DryerStat_avg(lastrow)
	variable lastrow

	string file_prefix="DryerStats_"
	Wave ACSM_UTC_Time=root:acsm_incoming:acsm_utc_time
	string DateFromTime=secs2date(acsm_utc_time[lastrow],-2)
	string DryerFileName=file_prefix+DateFromTime[0,3]+DateFromTime[5,6]+DateFromTime[8,9]+".txt"
	
	SVAR/Z DryerStat_path=root:ACMCC_Export:DryerStat_path
	NewPath/O/Q/Z DryerDataDir, DryerStat_path	
	KillDataFolder/Z root:DryerData
	NewDataFolder/O/S root:DryerData
	Make/O/N=1 RH_In_avg,T_In_avg,Dp_In_avg,RH_Out_Avg,T_Out_avg,Dp_Out_avg,FlowR_avg,P_Drop_avg
	GetFileFolderInfo/P=DryerDataDir/Q/Z DryerFileName
	if (V_flag!=0)
		print "Dryer file not found"
		return 0
	endif
	
	
	LoadWave /J/A/B="F=-2,N=DateTimeW;F=0,N=InletP;F=0,N=CounterP;F=0,N=PDrop;F=0,N=FlowRate;F=0,N=RHIn;F=0,N=TIn;F=0,N=RHDry;F=0,N=TDry;"/L={0,1,0,0,0}/D/O/P=DryerDataDir/Q DryerFileName
	wave DateTimeW
	TextWavesToDateTimeWave(dateTimeW, "DateTimeWave")
	wave DateTimeWave
	wave InletP,CounterP,PDrop,FlowRate,RHIn,TIn,RHDry,TDry
	concatenate /NP/KILL {DateTimeWave}, datW
	concatenate /NP/KILL {InletP}, InletPW
	concatenate /NP/KILL {CounterP}, CounterPW
	concatenate /NP/KILL {PDrop}, PDropW
	concatenate /NP/KILL {FlowRate}, FlowRateW
	concatenate /NP/KILL {RHIn}, RHInW
	concatenate /NP/KILL {TIn}, TInW		
	concatenate /NP/KILL {RHDry}, RHDryW
	concatenate /NP/KILL {TDry}, TDryW
	variable i,j
	string DateFromTimeBefore=secs2date(acsm_utc_time[lastrow-1],-2)
	string DryerFileNameBefore=file_prefix+DateFromTimeBefore[0,3]+DateFromTimeBefore[5,6]+DateFromTimeBefore[8,9]+".txt"
	
	if (!stringmatch(DryerFileName,DryerFileNameBefore))
		GetFileFolderInfo/P=DryerDataDir/Q/Z DryerFileNameBefore
		if (V_flag==0)
			LoadWave /J/A/B="F=-2,N=DateTimeW;F=0,N=InletP;F=0,N=CounterP;F=0,N=PDrop;F=0,N=FlowRate;F=0,N=RHIn;F=0,N=TIn;F=0,N=RHDry;F=0,N=TDry;"/L={0,1,0,0,0}/D/O/P=DryerDataDir/Q DryerFileNameBefore
			wave DateTimeW
			TextWavesToDateTimeWave(dateTimeW, "DateTimeWave")
			wave DateTimeWave
			wave InletP,CounterP,PDrop,FlowRate,RHIn,TIn,RHDry,TDry
			concatenate /NP/KILL {DateTimeWave}, datW
			concatenate /NP/KILL {InletP}, InletPW
			concatenate /NP/KILL {CounterP}, CounterPW
			concatenate /NP/KILL {PDrop}, PDropW
			concatenate /NP/KILL {FlowRate}, FlowRateW
			concatenate /NP/KILL {RHIn}, RHInW
			concatenate /NP/KILL {TIn}, TInW		
			concatenate /NP/KILL {RHDry}, RHDryW
			concatenate /NP/KILL {TDry}, TDryW
		endif
	endif
	make/O/N=(numpnts(RHInW)) dewPtInW = ACMCC_Calculate_Dp(RHInW, TInW)
	make/O/N=(numpnts(RHDryW)) dewPtDryW = ACMCC_Calculate_Dp(RHDryW, TDryW)
	duplicate/O dewPtInW dDewPtW
	dDewPtW -= dewPtDryW
	
	Make/O/N=1 RH_In_avg,T_In_avg,Dp_In_avg,RH_Out_Avg,T_Out_avg,Dp_Out_avg,FlowR_avg,P_Drop_avg
	i=BinarySearch(datW,acsm_utc_time[lastrow])
	j=BinarySearch(datW,acsm_utc_time[lastrow-1])
	
	if (i!=j)
		RH_In_avg=mean(RHInW,j,i)
		T_In_avg=mean(TInW,j,i)
		Dp_In_avg=mean(dewPtInW,j,i)
		RH_Out_Avg=mean(RHDryW,j,i)
		T_Out_avg=mean(TDryW,j,i)
		Dp_Out_avg=mean(dewPtDryW,j,i)
		FlowR_avg=mean(FlowRateW,j,i)
		P_Drop_avg=mean(PDropW,j,i)
	endif
	
End Function

Function ACMCC_Calculate_Dp(RH,T)
	variable RH, T
	variable dewPt
	DewPt = 243.04*(LN(RH/100)+((17.625*T)/(243.04+T)))/(17.625-LN(RH/100)-((17.625*T)/(243.04+T))) 
return dewPt
End

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





Function ConvertTextToDateTime(datetimeAsText)
    String datetimeAsText       // Assumed in YYYY-MM-DD format
   
    Variable dt
    Variable year, month, day, hour, minute, second
    sscanf datetimeAsText, "%d/%d/%d %d:%d:%d", day, month, year, hour, minute, second
    dt = Date2Secs(year, month, day)
    Variable timeOfDay
    timeOfDay = 3600*hour + 60*minute + second
   
    dt += timeOfDay
   
    return dt
End

Function/WAVE TextWavesToDateTimeWave(datetimeAsTextWave, outputWaveName)
    WAVE/T datetimeAsTextWave       // Assumed in YYYY-MM-DD format
    String outputWaveName

    Variable numPoints = numpnts(datetimeAsTextWave)
    Make/O/D/N=(numPoints) $outputWaveName
    WAVE wOut = $outputWaveName
    SetScale d, 0, 0, "dat", wOut
   
    Variable i
    for(i=0; i<numPoints; i+=1)
        String datetimeAsText = datetimeAsTextWave[i]
        Variable dt = ConvertTextToDateTime(datetimeAsText)
        wOut[i] = dt   
    endfor 
   
    return wOut
End

macro ACMCC_getConst_version_acsm()
	string/G root:ACMCC_Export:tempStr = versionStr
endmacro


function/t ACMCC_getConst_wrapper(exCall)
	//wrapper function for retrieving constants that may not exist (depending on which ipfs are present)
	string exCall //name of retrieval macro
	
	execute exCall+"()"
	svar tempStr = root:ACMCC_Export:tempStr
	string destStr = tempStr
	killstrings tempStr
	return destStr
end


Function/T ACMCC_MakeAndOrSetDF( data_folder )
	string data_folder
	
	string old_DF = GetDataFolder(1)
	setdatafolder root:
	if( !DataFolderExists( data_folder ) )
		NewDataFolder $data_folder
	endif
	SetDataFolder $data_folder
	return old_DF
End


Function FindYearToExport()

	NVAR/Z YearToExport=root:ACMCC_Export:YearToExport
	wave ACSM_time=root:ACSM_Incoming:acsm_utc_time
	
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