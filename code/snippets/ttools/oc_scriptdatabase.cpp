//********************************************************************
//
// File         : oc_scriptdatabase.cpp
// #   Copyright (C) 2014-2058 by
// #   Narayana Chikkam<nchikkam@gmail.com>
// #   All rights reserved.


#include "oc_scriptdatabase.h"

OC_CommonScriptsMap_t OC_ScriptInfo_c::m_CommonScriptsMap;
OC_CommonScriptsMap_t OC_ScriptInfo_c::m_SubScriptsMap;
static bool           g_FirstCall = true;  // To Skip the BRKVersionCheck for 1st Call And also Skipping Drive":"

#if defined(OC_OS_NW) || defined(OC_OS_OSF) || defined(OC_OS_OVMS)
  extern "C"
  {
    int errno;
  }
#endif //#ifdef OC_OS_NW


//********************************************************************
//
// Class	:           OC_Common_ScriptInfo_c
// Method	:
// Description	:
// Parameters	: <none>
// Returns	: <none>
// Comments	:
// Script Attributes Order in the CompressedFileHeader
// TYPE:             2
// VERSION:          3
// RTEVERSION:       4
// DEPENDENTSCRIPTS: 5
// DEVICEASSOC:      6
// BRKVERSION        7
// TESTNAME:         8
// TESTDESCR:        9
// TESTOPTION:       10
//
// Attributes Order in the m_Attributes Vector needs to follow the Order
// Of Enums.
  //CTor and Dtor
OC_Common_ScriptInfo_c::OC_Common_ScriptInfo_c
( void ) //Set the Hard Coded Attributes in m_Attributes vector
{
  //These Attributes are common for all the Scripts
  m_Attributes.push_back("TYPE:");
  m_Attributes.push_back("VERSION:");
  m_Attributes.push_back("RTEVERSION:");
  m_Attributes.push_back("BRKVERSION:");
  m_Attributes.push_back("DEPENDENTSCRIPTS:");
  m_Attributes.push_back("SUBSCRIPTS:"); //SubScripts Meta Attribute.
#if defined(OC_OS_OVMS)
 m_ScriptsRootDirectory = g_BuildPath(OC_PlatformFactory_c::m_pCurrent->Config_GetStringValue("Root Directory"), OC_IMMSTRING("scripts"), true);
#elif defined(OC_OS_NW)
  m_ScriptsRootDirectory = "sys:\\system\\nchikkam_tools\\scripts";
#else
  m_ScriptsRootDirectory = g_BuildPath(OC_PlatformFactory_c::m_pCurrent->Config_GetStringValue("Root Directory"), OC_IMMSTRING("scripts"));
#endif

  m_CommonAttributeCount = m_Attributes.size(); //minimum Count for all the ScriptObjects
}

OC_Common_ScriptInfo_c::~OC_Common_ScriptInfo_c
( ){}

//OverLoaded method to fill the datamembers with the passed Compression Header;
void  OC_Common_ScriptInfo_c::PopulateCommonMetaData( OC_Compression_c a_Comp, OC_String_t a_FileName  )
{
  OC_Byte_t*                                  a_pBuff = NULL;
  OC_ULong_t                                  a_BuffLen;
  OC_Compression_c::OC_CompressionHeader_t    a_Header;
  OC_String_t				                          a_TempStr;
  OC_String_t				                          a_DirName;
  OC_String_t				                          a_ScrName;

  a_Comp.ReadHeader(a_FileName,a_Header,a_pBuff,a_BuffLen); //ReadHeader

#ifdef OC_OS_OVMS
  // The script root direcotry will be SYS$SYSDEVICE:[XXXX.OPT.tools.scripts] .
  // The regular file and directory representation are different in OVMS.
  // regular file : SYS$SYSDEVICE:[XXXX.OPT.tools.scripts.common]utility.pm
  // directory file : SYS$SYSDEVICE:[XXXX.OPT.tools.scripts.common]
  // So to be consistent we store script name as UNIX file path i.e.,
  // for above example, 'common/utility.pm' instead of  'common]utility.pm'.

  a_TempStr = a_FileName.substr(m_ScriptsRootDirectory.size());
  a_ScrName = a_TempStr.substr(a_TempStr.find_last_of(OC_CHAR(']'))+1);
  a_ScrName = a_ScrName.substr(0, a_ScrName.find_first_of(OC_CHAR(';')));
  a_DirName = a_TempStr.substr(0, a_TempStr.find_last_of(OC_CHAR(']'))+1);

  a_DirName = g_ReplaceCharacter(a_DirName, OC_CHAR('.'), OC_CHAR('/'));
  a_DirName = g_ReplaceCharacter(a_DirName, OC_CHAR(']'), OC_CHAR('/'));

  SetScriptName (g_ToLowerCase(a_DirName+a_ScrName));
#else
  SetScriptName (  a_FileName.substr(m_ScriptsRootDirectory.size()+1 ));
#endif

  if(a_Comp.HasParam(2,a_pBuff,a_BuffLen))
    SetScriptType(a_Comp.GetSubParamStr(2,a_pBuff,a_BuffLen));
  if(a_Comp.HasParam(3,a_pBuff,a_BuffLen))
    SetScriptVersion(a_Comp.GetSubParamStr(3,a_pBuff,a_BuffLen));
  if(a_Comp.HasParam(4,a_pBuff,a_BuffLen))
    SetRTEVersion(a_Comp.GetSubParamStr(4,a_pBuff,a_BuffLen));

  if(a_Comp.HasParam(5, a_pBuff, a_BuffLen))
      GetAttributeValueList(a_Comp.GetSubParamStr(5, a_pBuff, a_BuffLen),
                     DependencyScriptsReference (), ',', true   );
  //@ToDo: BRKVERSION
  if(a_Comp.HasParam(7,a_pBuff,a_BuffLen))
    SetBrokenVersion(a_Comp.GetSubParamStr(7,a_pBuff,a_BuffLen));
  if(a_Comp.HasParam(12, a_pBuff, a_BuffLen))
      GetAttributeValueList(a_Comp.GetSubParamStr(12, a_pBuff, a_BuffLen),
                     SubScriptsReference() );

  if(a_pBuff)
    delete [] a_pBuff;
}

//OverLoaded method to fill the datamembers with the passed FileName;
void  OC_Common_ScriptInfo_c::PopulateCommonMetaData( OC_String_t      a_FileName )
{
  FILE*               a_pFileHandle           = NULL;
  OC_Char_t*          a_Buffer                = new char[g_MaxBufferLength];
  OC_String_t         a_Line ;
  OC_String_t         a_TempStr;
  OC_String_t         a_DirName;
  OC_String_t         a_ScrName;
  OC_ULong_t          a_AttrReadCount; // To Break the Loop Once all AttributesSet

  a_pFileHandle = OC_FOpen(a_FileName.c_str(),OC_IMMSTRING("r").c_str());
  if( a_pFileHandle !=  NULL  ) //Opened Successfully
  {
#ifdef OC_OS_OVMS
    // The script root direcotry will be SYS$SYSDEVICE:[XXXX.OPT.tools.scripts] .
    // The regular file and directory representation are different in OVMS.
    // regular file : SYS$SYSDEVICE:[XXXX.OPT.tools.scripts.common]utility.pm
    // directory file : SYS$SYSDEVICE:[XXXX.OPT.tools.scripts.common]
    // So to be consistent we store script name as UNIX file path i.e.,
    // for above example, 'common/utility.pm' instead of  'common]utility.pm'.

    a_TempStr = a_FileName.substr(m_ScriptsRootDirectory.size());
    a_ScrName = a_TempStr.substr(a_TempStr.find_last_of(OC_CHAR(']'))+1);
    a_ScrName = a_ScrName.substr(0, a_ScrName.find_first_of(OC_CHAR(';')));

    a_DirName = a_TempStr.substr(0, a_TempStr.find_last_of(OC_CHAR(']'))+1);
    a_DirName = g_ReplaceCharacter(a_DirName, OC_CHAR('.'), OC_CHAR('/'));
    a_DirName = g_ReplaceCharacter(a_DirName, OC_CHAR(']'), OC_CHAR('/'));

    SetScriptName (g_ToLowerCase(a_DirName+a_ScrName));
#else
    OC_String_t a_Temp = a_FileName.substr(m_ScriptsRootDirectory.size()+1 );
    SetScriptName (a_Temp );
#endif
    //Searching for the First Attribute.
    a_AttrReadCount = 0 ; //This should be 0 for commonScripts
    while( fgets( a_Buffer, g_MaxBufferLength, a_pFileHandle ) )
    {
      a_Line = g_StripCharacter(a_Buffer,'\n');
      if ( a_Line.find( m_Attributes.at( OC_ScriptAttribute_Type_e ))  != string::npos )
      {
          SetScriptType(  GetAttributeValue(a_Line, m_Attributes.at( OC_ScriptAttribute_Type_e )));
          a_AttrReadCount++;
      }
      else //The order RTEVersion and Version Matters here since "RTEVERSION" also Contains "VERISON"
      if ( a_Line.find( m_Attributes.at( OC_ScriptAttribute_RTEVersion_e )) != string::npos  )
      {
          SetRTEVersion( GetAttributeValue(a_Line, m_Attributes.at( OC_ScriptAttribute_RTEVersion_e ) ) );
          a_AttrReadCount++;
      }
      else
      if ( a_Line.find( m_Attributes.at( OC_ScriptAttribute_Version_e )) != string::npos  )
      {
          SetScriptVersion( GetAttributeValue(a_Line, m_Attributes.at( OC_ScriptAttribute_Version_e ) ) );
          a_AttrReadCount++;
      }

      else
      if ( a_Line.find( m_Attributes.at( OC_ScriptAttribute_DependentScripts_e )) != string::npos  )
      {
            GetAttributeValueList(GetAttributeValue(a_Line,m_Attributes.at(OC_ScriptAttribute_DependentScripts_e)),
              DependencyScriptsReference(), ',', true );
            a_AttrReadCount++;
      }
      else
      if ( a_Line.find( m_Attributes.at( OC_ScriptAttribute_BRKVersion_e )) != string::npos  )
      {
          SetBrokenVersion( GetAttributeValue(a_Line, m_Attributes.at( OC_ScriptAttribute_BRKVersion_e ) ) );
          a_AttrReadCount++;
      }
      else
      if ( a_Line.find( m_Attributes.at( OC_ScriptAttribute_SubScripts_e )) != string::npos  )
      {
          GetAttributeValueList(GetAttributeValue(a_Line,m_Attributes.at(OC_ScriptAttribute_SubScripts_e)),
              SubScriptsReference() );
          a_AttrReadCount++;
      }
      if( a_AttrReadCount == m_CommonAttributeCount ) // const = 5
      { //All the Attributes Set; Leave the Loop
        break;
      }
    }//While
    OC_FClose(a_pFileHandle);
  }
  if(a_Buffer)
    delete []a_Buffer;
}

//********************************************************************
//
// Class	:           OC_Common_ScriptInfo_c
// Method	:           GetAttributeValue
// Description	:
// Parameters	:       a_Line, a_AttrName
// Returns	:         AttributeValue
// Comments:          Given a Line readfrom the file and the Attribute,
//                    this function returns the value associated to that
//                    Attribute. Ex: Attribute:
//                    line = DEVICEASSOC: nchikkamUltrium 2-SCSI
//                    This function returns "nchikkamUltrium 2-SCSI".
OC_String_t OC_Common_ScriptInfo_c::GetAttributeValue
(OC_String_t a_Line,
 OC_String_t a_AttrName )
{
  OC_Long_t   a_Position = -1;
  OC_ULong_t  a_Index;
  OC_String_t a_ReturnString;
  OC_String_t a_TempStr;

  a_Position = a_Line.find(a_AttrName);
  a_TempStr = a_ReturnString = a_Line.substr( a_Position + a_AttrName.length () );
  //before processing further check the value is specified for lable or NOT
  //Removing Leading Spaces.
  a_Index = 0;
  while(a_Index < a_TempStr.size())
  {
    if(a_TempStr.at(a_Index) == ' '|| a_TempStr.at(a_Index) == '\t')
    {
      a_ReturnString = a_TempStr.substr(a_Index +1);
      a_Index++;
    }
    else
      break;
  }
  if(a_ReturnString.size() == 0)
  {
    //publish message and throw an execption...
    OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg_P2(OC_MSGSET_SCRIPT_DATABASE,OC_MSG_SCRIPT_DATABASE_METADATA_VALUE_ERROR,"MetaData",
                      a_AttrName.substr(0,a_AttrName.size()-1), "Filename",GetScriptName()),0,0,NULL,OC_Event_c::OC_DetailLevel_2_e,8,NULL,NULL);
    throw OC_Exception_c(false,OC_ExOrigin_FrameWork_e,OC_ExCode_InternalFailure_e);
  }

  //Removing Trailing Spaces. Scripts Embedded in the Firmware[.frm] files could have any 'white space' at the end of the String
  for(a_Index = a_ReturnString.size()-1 ; a_Index > 0;   )
  {
	  if (a_ReturnString.at(a_Index) == ' '  ||
        a_ReturnString.at(a_Index) == '\t' ||
        a_ReturnString.at(a_Index) == '\n' ||
        a_ReturnString.at(a_Index) == '\r' ||
        a_ReturnString.at(a_Index) == '\0'   )
		  a_Index--;
	  else
	    break;
  }
  //Removing Trailing Spaces.
  a_ReturnString = a_ReturnString.substr(0,a_Index+1);
  //If attribute is of type 'TESTOPTINT' OR TESTOPTEXT',
  //then return complete string not only just value..
  if(strcmp(a_AttrName.c_str(), "TESTOPTINT:") == 0 || strcmp(a_AttrName.c_str(), "TESTOPTEXT:") == 0)
    a_ReturnString = a_AttrName + a_ReturnString;
  return a_ReturnString;
}


// Constructs the Strings List and returns the Array.
// Second argument is a reference to modify the passed one.
// ForEg: tempString = common/oc_lib_tool_xs.pm,common/utility.pm,common/datafile.pm
// This funtion returns a vector of Strings as:
//                                  common/oc_lib_tool_xs.pm
//                                  common/utility.pm
//                                  common/datafile.pm
//
void OC_Common_ScriptInfo_c::GetAttributeValueList
( OC_String_t       a_ValueString,
  OC_StringList_t&  a_ReturnList,
  OC_Char_t         a_Delimetere,
  bool              a_FlagDepList )
{
  //  Steps:
  //  while( EOF(STRING) )
  //  {
  //    if char is '('
  //    {
  //      Reach till ).
  //      Push it into Vector.
  //    }
  //    else
  //    {
  //      if( char is ',' )
  //      {
  //        Push the substr(line, 0, posOf(,)-1) into the Vector.
  //      }
  //    }
  //  }

  OC_ULong_t   a_Index;
  bool         a_FlagComma = true;

  if( a_FlagDepList == true )
  {
    OC_ULong_t   a_StPos = 0;
    OC_String_t  a_TempStr;
    for( a_Index = 0 ; a_Index < a_ValueString.size() ; )
    {
      if( a_ValueString.at(a_Index) == '(' )
      {
        while( a_ValueString.at(a_Index++) != ')' );
        a_TempStr = a_ValueString.substr(a_StPos, a_Index - a_StPos );
        a_ReturnList.push_back( a_TempStr  );
        a_StPos = a_Index+1; //  Skipping the Comma","
        a_FlagComma = false;
      }
      else
      {
        if( a_ValueString.at(a_Index) == ',' )
        {
          a_TempStr = a_ValueString.substr(a_StPos, a_Index - a_StPos );
          a_ReturnList.push_back( a_TempStr  );
          a_StPos = a_Index+1; // Skipping the Comma","
          a_FlagComma = true;
        }
      }
      ++a_Index;
    }
    if( a_StPos < a_ValueString.size() )
    {
      a_TempStr = a_ValueString.substr(a_StPos, a_Index - a_StPos );
      a_ReturnList.push_back( a_TempStr  );
    }

  }
  else
  {
    g_ParseSeparatorString( a_ValueString,
                            a_Delimetere,
                            a_ReturnList,
                            false,
                            false );
  }

  for( a_Index = 0 ; a_Index < a_ReturnList.size()  ; a_Index ++ )
  {
#if defined(OC_OS_WINDOWS) || defined(OC_OS_NW) //Replacing the Directory Seperator wrt RunTime OS
      a_ReturnList.at(a_Index) = g_ReplaceCharacter( a_ReturnList.at(a_Index), OC_CHAR('/'), OC_CHAR('\\'));
#else
      a_ReturnList.at(a_Index) = g_ReplaceCharacter( a_ReturnList.at(a_Index), OC_CHAR('\\'), OC_CHAR('/'));
#endif
  }
}


//Fills the datamembers with the info from the MetaData present in the file a_FileName
void OC_Common_ScriptInfo_c::ReadMetaData
( OC_String_t  a_FileName, OC_Char_t a_Delimetere )
{
  OC_Compression_c                            a_Comp;
  OC_Compression_c::OC_CompressionHeader_t    a_Header;
  OC_Byte_t*                                  a_pBuff = NULL;
  OC_ULong_t                                  a_BuffLen;
  if(a_Comp.ReadHeader(a_FileName,a_Header,a_pBuff,a_BuffLen))
  { //No Need to Open the File; Just read the information from Compressed Header;
    //the file was compressed
    PopulateCommonMetaData(a_Comp, a_FileName );
    if(a_pBuff)
      delete [] a_pBuff;
  }
  else
  { // the file was not compressed
    PopulateCommonMetaData(a_FileName);
  }

}


//********************************************************************
//
// Class	:         OC_DataAcquisition_ScriptInfo_c
// Method	:
// Description	:
// Parameters	: <none>
// Returns	: <none>
// Comments	:
OC_DataAcquisition_ScriptInfo_c::OC_DataAcquisition_ScriptInfo_c
(  void   ) //Calls super to set the attributes.
{

    m_Attributes.push_back ("DEVICEASSOC:");
}
OC_DataAcquisition_ScriptInfo_c::~OC_DataAcquisition_ScriptInfo_c(){}


void   OC_DataAcquisition_ScriptInfo_c::ReadMetaData
( OC_String_t  a_FileName, OC_Char_t a_Delimetere  )
{
  FILE*                                       a_pFileHandle     = NULL;
  OC_Compression_c                            a_Comp;
  OC_Compression_c::OC_CompressionHeader_t    a_Header;
  OC_Byte_t*                                  a_pBuff = NULL;
  OC_ULong_t                                  a_BuffLen;
  OC_Char_t*                                  a_Buffer          = new char[g_MaxBufferLength];
  OC_String_t                                 a_Line ;
  OC_ULong_t                                  a_AttrReadCount; // To Break the Loop Once all AttributesSet

  if(a_Comp.ReadHeader(a_FileName,a_Header,a_pBuff,a_BuffLen))
  { //No Need to Open the File; Just read the information from Compressed Header;
    //the file was compressed

    PopulateCommonMetaData(a_Comp, a_FileName ); //CommonMetaData
    if(a_Comp.HasParam(5, a_pBuff, a_BuffLen))
      GetAttributeValueList(a_Comp.GetSubParamStr(5, a_pBuff, a_BuffLen),
                     DependencyScriptsReference () );
    //DevAssociation
    if(a_Comp.HasParam(6, a_pBuff, a_BuffLen))
      g_ParseSeparatorString(a_Comp.GetSubParamStr(6, a_pBuff, a_BuffLen),
                                     a_Delimetere,
                                     m_DeviceAssocList,
                                     false,
                                     false );
    if(a_pBuff)
      delete [] a_pBuff;
  }
  else
  { // the file was not compressed
    PopulateCommonMetaData(a_FileName); //ReadCommon MetaInfo
    a_pFileHandle = OC_FOpen(a_FileName.c_str(),OC_IMMSTRING("r").c_str());
    if( a_pFileHandle !=  NULL  ) //Opened Successfully
    {
      a_AttrReadCount = m_CommonAttributeCount ;

      while( fgets( a_Buffer, g_MaxBufferLength, a_pFileHandle ) )
      {
        a_Line = g_StripCharacter(a_Buffer,'\n');
        if ( a_Line.find( m_Attributes.at( OC_ScriptAttribute_DeviceAssoc_e )) != string::npos  )
        {
            g_ParseSeparatorString(  GetAttributeValue(a_Line,m_Attributes.at(OC_ScriptAttribute_DeviceAssoc_e)),
                                     a_Delimetere,
                                     m_DeviceAssocList,
                                     false,
                                     false );
            a_AttrReadCount++;
        }
        if( a_AttrReadCount == m_Attributes.size() )
        { //All the Attributes Set; Leave the Loop
          break;
        }
      }//While
      OC_FClose(a_pFileHandle);
    }
  }
  if(a_Buffer)
    delete []a_Buffer;
}


//********************************************************************
//
// Class	:        OC_Test_ScriptInfo_c
// Method	:
// Description	:
// Parameters	: <none>
// Returns	: <none>
// Comments	:
//  Additional attributes:
//              "DEVICEASSOC:"
//              "TESTOPTION:"
//              "TESTDESCRIPTION:"
//              "TESTNAME:"

OC_Test_ScriptInfo_c::OC_Test_ScriptInfo_c
(  void   ) //Calls parentCtor and populates
{                                                     //the vector with test Attributes
    m_Attributes.push_back("DEVICEASSOC:");
    m_Attributes.push_back("TESTNAME:");
    m_Attributes.push_back("TESTDESCR:");
    //m_Attributes.push_back("TESTOPTION:");
    m_Attributes.push_back("TESTOPTINT:");
    m_Attributes.push_back("TESTOPTEXT:");
}
OC_Test_ScriptInfo_c::~OC_Test_ScriptInfo_c
(  void   ){}

void OC_Test_ScriptInfo_c::ReadMetaData
( OC_String_t  a_FileName, OC_Char_t a_Delimetere  )
{
  FILE*                                       a_pFileHandle     = NULL;
  OC_Compression_c                            a_Comp;
  OC_Compression_c::OC_CompressionHeader_t    a_Header;
  OC_Byte_t*                                  a_pBuff = NULL;
  OC_ULong_t                                  a_BuffLen;
  OC_Char_t*                                  a_Buffer          = new char[g_MaxBufferLength];
  OC_String_t                                 a_Line ;
  OC_ULong_t                                  a_AttrReadCount; // To Break the Loop Once all AttributesSet

  if(a_Comp.ReadHeader(a_FileName,a_Header,a_pBuff,a_BuffLen))
  { //No Need to Open the File; Just read the information from Compressed Header;
    //the file was compressed
    PopulateCommonMetaData(a_Comp, a_FileName ); //CommonMetaData
    //DevAssociation
    if(a_Comp.HasParam(6, a_pBuff, a_BuffLen))
      g_ParseSeparatorString(a_Comp.GetSubParamStr(6, a_pBuff, a_BuffLen),
                                     a_Delimetere,
                                     m_DeviceAssocList,
                                     false,
                                     false );
    if(a_Comp.HasParam(8,a_pBuff,a_BuffLen))
      SetTestName(a_Comp.GetSubParamStr(8,a_pBuff,a_BuffLen));
    if(a_Comp.HasParam(9,a_pBuff,a_BuffLen))
      SetTestDescription(a_Comp.GetSubParamStr(9,a_pBuff,a_BuffLen));

    //Get the list of Internal and External test options if there..
    a_Comp.GetSubParamsStr("TESTOPTINT", m_TestIntOption,a_pBuff,a_BuffLen);

    a_Comp.GetSubParamsStr("TESTOPTEXT", m_TestExtOption,a_pBuff,a_BuffLen);

    if(a_pBuff)
      delete [] a_pBuff;
  }
  else
  { // the file was not compressed
    PopulateCommonMetaData(a_FileName); //ReadCommon MetaInfo
    a_pFileHandle = OC_FOpen(a_FileName.c_str(),OC_IMMSTRING("r").c_str());
    if( a_pFileHandle !=  NULL  ) //Opened Successfully
    {
      a_AttrReadCount = m_CommonAttributeCount ;

      while( fgets( a_Buffer, g_MaxBufferLength, a_pFileHandle ) )
      {
        a_Line = g_StripCharacter(a_Buffer,'\n');
        if ( a_Line.find( m_Attributes.at( OC_ScriptAttribute_DeviceAssoc_e )) != string::npos  )
        {
            g_ParseSeparatorString (GetAttributeValue(a_Line,m_Attributes.at(OC_ScriptAttribute_DeviceAssoc_e)),
                                     a_Delimetere,
                                     m_DeviceAssocList,
                                     false,
                                     false );
        }
        else
        if ( a_Line.find( m_Attributes.at( OC_ScriptAttribute_TestName_e )) != string::npos  )
        {
            SetTestName( GetAttributeValue(a_Line, m_Attributes.at( OC_ScriptAttribute_TestName_e ) ) );
            a_AttrReadCount++;
        }
        else
        if ( a_Line.find( m_Attributes.at( OC_ScriptAttribute_TestIntOption_e )) != string::npos  )
        {
           //Internal option.
            //SetTestOption(GetAttributeValue(a_Line, m_Attributes.at( OC_ScriptAttribute_TestOption_e)) );
          SetTestOption(OC_Internal_e,GetAttributeValue(a_Line, m_Attributes.at( OC_ScriptAttribute_TestIntOption_e)) );
            a_AttrReadCount++;
        }
        else
        if ( a_Line.find( m_Attributes.at( OC_ScriptAttribute_TestExtOption_e )) != string::npos  )
        {
          //External option.
            //SetTestOption(GetAttributeValue(a_Line, m_Attributes.at( OC_ScriptAttribute_TestOption_e)) );
          SetTestOption(OC_External_e,GetAttributeValue(a_Line, m_Attributes.at( OC_ScriptAttribute_TestExtOption_e)) );
            a_AttrReadCount++;
        }
        else
        if ( a_Line.find( m_Attributes.at( OC_ScriptAttribute_TestDescription_e )) != string::npos  )
        {
            SetTestDescription(GetAttributeValue(a_Line, m_Attributes.at( OC_ScriptAttribute_TestDescription_e)) );
            a_AttrReadCount++;
        }

      }//While
      OC_FClose(a_pFileHandle);
    }
  }
  if(a_Buffer)
    delete []a_Buffer;
}


void OC_Test_ScriptInfo_c::SetTestOption
(OC_Option_type_t Optiontype,
 OC_String_t      Option)
{
  switch(Optiontype)
  {
    case OC_Internal_e:
      m_TestIntOption.push_back(Option);
      break;
    case OC_External_e:
      m_TestExtOption.push_back(Option);
      break;
    default:
      break;
  }
  return;
}


OC_StringList_t  OC_Test_ScriptInfo_c::GetTestOption
(OC_Option_type_t  Optiontype)
{
  OC_StringList_t     Options;
  switch(Optiontype)
  {
    case OC_Internal_e:
      return m_TestIntOption;
    case OC_External_e:
      return m_TestExtOption;
    default:
      return Options;
  }
}

//********************************************************************
//
// Class	:      OC_FWUpdate_ScriptInfo_c
// Method	:
// Description	:
// Parameters	: <none>
// Returns	: <none>
// Comments	:

OC_FWUpdate_ScriptInfo_c::OC_FWUpdate_ScriptInfo_c
(  void   ) //Calls super to set the attributes.
{   //Set FWUpdate Specific Attributes here.
    m_Attributes.push_back("DEVICEASSOC:");
}

OC_FWUpdate_ScriptInfo_c::~OC_FWUpdate_ScriptInfo_c
(  void   ){}

void OC_FWUpdate_ScriptInfo_c::ReadMetaData
( OC_String_t  a_FileName, OC_Char_t a_Delimetere  )
{
  FILE*                                       a_pFileHandle     = NULL;
  OC_Compression_c                            a_Comp;
  OC_Compression_c::OC_CompressionHeader_t    a_Header;
  OC_Byte_t*                                  a_pBuff = NULL;
  OC_ULong_t                                  a_BuffLen;
  OC_Char_t*                                  a_Buffer          = new char[g_MaxBufferLength];
  OC_String_t                                 a_Line ;
  OC_ULong_t                                  a_AttrReadCount; // To Break the Loop Once all AttributesSet

  if(a_Comp.ReadHeader(a_FileName,a_Header,a_pBuff,a_BuffLen))
  { //No Need to Open the File; Just read the information from Compressed Header;
    //the file was compressed
    PopulateCommonMetaData(a_Comp, a_FileName ); //CommonMetaData
    //DevAssociation
    if(a_Comp.HasParam(6, a_pBuff, a_BuffLen))
      g_ParseSeparatorString(a_Comp.GetSubParamStr(6, a_pBuff, a_BuffLen),
                                     a_Delimetere,
                                     m_DeviceAssocList,
                                     false,
                                     false );
    if(a_pBuff)
      delete [] a_pBuff;
  }
  else
  { // the file was not compressed
    PopulateCommonMetaData(a_FileName); //ReadCommon MetaInfo
    a_pFileHandle = OC_FOpen(a_FileName.c_str(),OC_IMMSTRING("r").c_str());
    if( a_pFileHandle !=  NULL  ) //Opened Successfully
    {
      a_AttrReadCount = m_CommonAttributeCount ;

      while( fgets( a_Buffer, g_MaxBufferLength, a_pFileHandle ) )
      {
        a_Line = g_StripCharacter(a_Buffer,'\n');
        if ( a_Line.find( m_Attributes.at( OC_ScriptAttribute_DeviceAssoc_e )) != string::npos  )
        {
            g_ParseSeparatorString (GetAttributeValue(a_Line,m_Attributes.at(OC_ScriptAttribute_DeviceAssoc_e)),
                                     a_Delimetere,
                                     m_DeviceAssocList,
                                     false,
                                     false );
        }
        if( a_AttrReadCount == m_Attributes.size() )
        { //All the Attributes Set; Leave the Loop
          break;
        }
      }//While
      OC_FClose(a_pFileHandle);
    }
  }
  if(a_Buffer)
    delete []a_Buffer;
}


//********************************************************************
//
// Class	:         OC_Decode_ScriptInfo_c
// Method	:
// Description	:
// Parameters	: <none>
// Returns	: <none>
// Comments	:

OC_Decode_ScriptInfo_c::OC_Decode_ScriptInfo_c
(  void ) //Calls super to set the attributes.
{
    m_Attributes.push_back("DEVICEASSOC:");
}
OC_Decode_ScriptInfo_c::~OC_Decode_ScriptInfo_c
(  void   ){}

void OC_Decode_ScriptInfo_c::ReadMetaData
( OC_String_t  a_FileName, OC_Char_t a_Delimetere  )
{
  FILE*                                       a_pFileHandle     = NULL;
  OC_Compression_c                            a_Comp;
  OC_Compression_c::OC_CompressionHeader_t    a_Header;
  OC_Byte_t*                                  a_pBuff = NULL;
  OC_ULong_t                                  a_BuffLen;
  OC_Char_t*                                  a_Buffer          = new char[g_MaxBufferLength];
  OC_String_t                                 a_Line ;
  OC_ULong_t                                  a_AttrReadCount; // To Break the Loop Once all AttributesSet

  if(a_Comp.ReadHeader(a_FileName,a_Header,a_pBuff,a_BuffLen))
  { //No Need to Open the File; Just read the information from Compressed Header;
    //the file was compressed
    PopulateCommonMetaData(a_Comp, a_FileName ); //CommonMetaData
    //DevAssociation
    if(a_Comp.HasParam(6, a_pBuff, a_BuffLen))
      g_ParseSeparatorString(a_Comp.GetSubParamStr(6, a_pBuff, a_BuffLen),
                                     a_Delimetere,
                                     m_DeviceAssocList,
                                     false,
                                     false );
    if(a_pBuff)
      delete [] a_pBuff;
  }
  else
  { // the file was not compressed
    PopulateCommonMetaData(a_FileName); //ReadCommon MetaInfo
    a_pFileHandle = OC_FOpen(a_FileName.c_str(),OC_IMMSTRING("r").c_str());
    if( a_pFileHandle !=  NULL  ) //Opened Successfully
    {
      a_AttrReadCount = m_CommonAttributeCount ;
      while( fgets( a_Buffer, g_MaxBufferLength, a_pFileHandle ) )
      {
        a_Line = g_StripCharacter(a_Buffer,'\n');
        if ( a_Line.find( m_Attributes.at( OC_ScriptAttribute_DeviceAssoc_e )) != string::npos  )
        {
            g_ParseSeparatorString (GetAttributeValue(a_Line,m_Attributes.at(OC_ScriptAttribute_DeviceAssoc_e)),
                                     a_Delimetere,
                                     m_DeviceAssocList,
                                     false,
                                     false );
        }
        if( a_AttrReadCount == m_Attributes.size() )
        { //All the Attributes Set; Leave the Loop
          break;
        }
      }//While
      OC_FClose(a_pFileHandle);
    }
  }
  if(a_Buffer)
    delete []a_Buffer;
}


//********************************************************************
//
// Class	:      OC_Parse_ScriptInfo_c
// Method	:
// Description	:
// Parameters	: <none>
// Returns	: <none>
// Comments	:

OC_Parse_ScriptInfo_c::OC_Parse_ScriptInfo_c
(  void   ) //Calls super to set the attributes.
{
    m_Attributes.push_back ("DEVICEASSOC:");
}
OC_Parse_ScriptInfo_c::~OC_Parse_ScriptInfo_c
(  void   ){}

void OC_Parse_ScriptInfo_c::ReadMetaData
( OC_String_t  a_FileName, OC_Char_t a_Delimetere  )
{
  FILE*                                       a_pFileHandle     = NULL;
  OC_Compression_c                            a_Comp;
  OC_Compression_c::OC_CompressionHeader_t    a_Header;
  OC_Byte_t*                                  a_pBuff = NULL;
  OC_ULong_t                                  a_BuffLen;
  OC_Char_t*                                  a_Buffer          = new char[g_MaxBufferLength];
  OC_String_t                                 a_Line ;
  OC_ULong_t                                  a_AttrReadCount; // To Break the Loop Once all AttributesSet

  if(a_Comp.ReadHeader(a_FileName,a_Header,a_pBuff,a_BuffLen))
  { //No Need to Open the File; Just read the information from Compressed Header;
    //the file was compressed
    PopulateCommonMetaData(a_Comp, a_FileName ); //CommonMetaData
    //DevAssociation
    if(a_Comp.HasParam(6, a_pBuff, a_BuffLen))
      g_ParseSeparatorString(a_Comp.GetSubParamStr(6, a_pBuff, a_BuffLen),
                                     a_Delimetere,
                                     m_DeviceAssocList,
                                     false,
                                     false );
    if(a_pBuff)
      delete [] a_pBuff;
  }
  else
  { // the file was not compressed
    PopulateCommonMetaData(a_FileName); //ReadCommon MetaInfo
    a_pFileHandle = OC_FOpen(a_FileName.c_str(),OC_IMMSTRING("r").c_str());
    if( a_pFileHandle !=  NULL  ) //Opened Successfully
    {
      a_AttrReadCount = m_CommonAttributeCount ;
      while( fgets( a_Buffer, g_MaxBufferLength, a_pFileHandle ) )
      {
        a_Line = g_StripCharacter(a_Buffer,'\n');
        if ( a_Line.find( m_Attributes.at( OC_ScriptAttribute_DeviceAssoc_e )) != string::npos  )
        {
            g_ParseSeparatorString (GetAttributeValue(a_Line,m_Attributes.at(OC_ScriptAttribute_DeviceAssoc_e)),
                                     a_Delimetere,
                                     m_DeviceAssocList,
                                     false,
                                     false );
        }
        if( a_AttrReadCount == m_Attributes.size() )
        { //All the Attributes Set; Leave the Loop
          break;
        }
      }//While
      OC_FClose(a_pFileHandle);
    }
  }
  if(a_Buffer)
    delete []a_Buffer;
}

//********************************************************************
//
// Class	:     OC_STicket_ScriptInfo_c
// Method	:
// Description	:
// Parameters	: <none>
// Returns	: <none>
// Comments	:

OC_STicket_ScriptInfo_c::OC_STicket_ScriptInfo_c
(  void ) //Calls super to set the attributes.
{
  m_Attributes.push_back ("DEVICEASSOC:");
}
OC_STicket_ScriptInfo_c::~OC_STicket_ScriptInfo_c
(  void ){}

void OC_STicket_ScriptInfo_c::ReadMetaData
( OC_String_t  a_FileName, OC_Char_t a_Delimetere  )
{
  FILE*                                       a_pFileHandle     = NULL;
  OC_Compression_c                            a_Comp;
  OC_Compression_c::OC_CompressionHeader_t    a_Header;
  OC_Byte_t*                                  a_pBuff = NULL;
  OC_ULong_t                                  a_BuffLen;
  OC_Char_t*                                  a_Buffer          = new char[g_MaxBufferLength];
  OC_String_t                                 a_Line ;
  OC_ULong_t                                  a_AttrReadCount; // To Break the Loop Once all AttributesSet

  if(a_Comp.ReadHeader(a_FileName,a_Header,a_pBuff,a_BuffLen))
  { //No Need to Open the File; Just read the information from Compressed Header;
    //the file was compressed
    PopulateCommonMetaData(a_Comp, a_FileName ); //CommonMetaData
    //DevAssociation
    if(a_Comp.HasParam(6, a_pBuff, a_BuffLen))
      g_ParseSeparatorString(a_Comp.GetSubParamStr(6, a_pBuff, a_BuffLen),
                                     a_Delimetere,
                                     m_DeviceAssocList,
                                     false,
                                     false );
    if(a_pBuff)
      delete [] a_pBuff;
  }
  else
  { // the file was not compressed
    PopulateCommonMetaData(a_FileName); //ReadCommon MetaInfo
    a_pFileHandle = OC_FOpen(a_FileName.c_str(),OC_IMMSTRING("r").c_str());
    if( a_pFileHandle !=  NULL  ) //Opened Successfully
    {
      a_AttrReadCount = m_CommonAttributeCount ;
      while( fgets( a_Buffer, g_MaxBufferLength, a_pFileHandle ) )
      {
        a_Line = g_StripCharacter(a_Buffer,'\n');
        if ( a_Line.find( m_Attributes.at( OC_ScriptAttribute_DeviceAssoc_e )) != string::npos  )
        {
            g_ParseSeparatorString (GetAttributeValue(a_Line,m_Attributes.at(OC_ScriptAttribute_DeviceAssoc_e)),
                                     a_Delimetere,
                                     m_DeviceAssocList,
                                     false,
                                     false );
            a_AttrReadCount++;
        }
        if( a_AttrReadCount == m_Attributes.size() )
        { //All the Attributes Set; Leave the Loop
          break;
        }
      }//While
      OC_FClose(a_pFileHandle);
    }
  }
  if(a_Buffer)
    delete []a_Buffer;
}

//********************************************************************
//
// Class	:  OC_ScriptInfo_c
// Method	:
// Description	:
// Parameters	: <none>
// Returns	: <none>
// Comments	:
//Checks in all the Maps for a_ScriptName and if found in any one of the Maps, the
//Corresponding Object is returned.

OC_ScriptInfo_c::OC_ScriptInfo_c
( void   )   //By default all the maps are of size 0
{
}

OC_ScriptInfo_c::~OC_ScriptInfo_c
( void   )
{
  //Clear All the Maps
}

OC_Common_ScriptInfo_c*   OC_ScriptInfo_c::GetObject
( OC_String_t a_ScriptName )
{

#ifdef OC_OS_OVMS
  a_ScriptName = g_ToLowerCase(a_ScriptName);
#endif

  OC_Common_ScriptInfo_c *            a_ReturnObject          = NULL;
  a_ReturnObject  = GetCommonObject ( a_ScriptName );
  if (  a_ReturnObject != NULL ){ return a_ReturnObject;  }
  a_ReturnObject  = GetDataAcqObject( a_ScriptName );
  if (  a_ReturnObject != NULL ){ return a_ReturnObject;  }
  a_ReturnObject  = GetDecodeObject ( a_ScriptName );
  if (  a_ReturnObject != NULL ){ return a_ReturnObject;  }
  a_ReturnObject  = GetParseObject  ( a_ScriptName );
  if (  a_ReturnObject != NULL ){ return a_ReturnObject;  }
  a_ReturnObject  = GetSTicketObject ( a_ScriptName );
  if (  a_ReturnObject != NULL ){ return a_ReturnObject;  }
  a_ReturnObject  = GetTestObject ( a_ScriptName );
  if (  a_ReturnObject != NULL ){ return a_ReturnObject;  }
  a_ReturnObject  = GetFWUpdateObject ( a_ScriptName );
  if (  a_ReturnObject != NULL ){ return a_ReturnObject;  }
  a_ReturnObject  = GetSubScriptObject ( a_ScriptName );
  if (  a_ReturnObject != NULL ){ return a_ReturnObject;  }
  return a_ReturnObject;
}

//Returns an Object of OC_Common_ScriptInfo Whose key is a_ScriptName in the CommonMap
OC_Common_ScriptInfo_c* OC_ScriptInfo_c::GetCommonObject
( OC_String_t a_ScriptName  )
{
  OC_Common_ScriptInfo_c*             a_ReturnObject = NULL;
  OC_CommonScriptsMap_t::iterator     a_Iter;

  //Check if g is present at end,
  a_Iter = m_CommonScriptsMap.find( a_ScriptName );
  if( a_Iter != m_CommonScriptsMap.end() )
  {
    a_ReturnObject = a_Iter->second;
  }
  if( a_ReturnObject == NULL ) //.XX is not found in Map i.e, files are compressed, search for .XXg
  {
    if( a_ScriptName.at( a_ScriptName.size()-1) != 'g')
    {
      a_ScriptName += "g";
      a_Iter = m_CommonScriptsMap.find( a_ScriptName );
      if( a_Iter != m_CommonScriptsMap.end() )
      {
        a_ReturnObject = a_Iter->second;
      }
    }
  }
  return a_ReturnObject;
}

//Returns an Object of OC_Common_ScriptInfo Whose key is a_ScriptName in the SubScriptsMap
OC_Common_ScriptInfo_c* OC_ScriptInfo_c::GetSubScriptObject
( OC_String_t a_ScriptName  )
{
  OC_Common_ScriptInfo_c*             a_ReturnObject = NULL;
  OC_SubScriptsMap_t::iterator        a_Iter;

  //Check if g is present at end,
  a_Iter = m_SubScriptsMap.find( a_ScriptName );
  if( a_Iter != m_SubScriptsMap.end() )
  {
    a_ReturnObject = a_Iter->second;
  }
  if( a_ReturnObject == NULL ) //.XX is not found in Map i.e, files are compressed, search for .XXg
  {
    if( a_ScriptName.at( a_ScriptName.size()-1) != 'g' )
    {
      a_ScriptName += "g";
      a_Iter = m_SubScriptsMap.find( a_ScriptName );
      if( a_Iter != m_SubScriptsMap.end() )
      {
        a_ReturnObject = a_Iter->second;
      }
    }
  }
  return a_ReturnObject;
}


//Returns an Object of OC_STicket_ScriptInfo Whose key is a_ScriptName in the STicketMap
OC_STicket_ScriptInfo_c*    OC_ScriptInfo_c::GetSTicketObject
( OC_String_t a_ScriptName  )
{
  OC_STicket_ScriptInfo_c * a_ReturnObject = NULL;
  OC_STicketScriptsMap_t::iterator a_Iter;
  a_Iter = m_STicketScriptsMap.find( a_ScriptName );
  if( a_Iter != m_STicketScriptsMap.end() )
  {
    a_ReturnObject = (OC_STicket_ScriptInfo_c*)a_Iter->second;
  }
  if( a_ReturnObject == NULL ) //.XX is not found in Map i.e, files are compressed, search for .XXg
  {
    if( a_ScriptName.at( a_ScriptName.size()-1) != 'g' )
    {
      a_ScriptName += "g";
      a_Iter = m_STicketScriptsMap.find( a_ScriptName );
      if( a_Iter != m_STicketScriptsMap.end() )
      {
        a_ReturnObject = (OC_STicket_ScriptInfo_c*)a_Iter->second;
      }
    }
  }

  return a_ReturnObject;
}


//Returns an Object of OC_FWUpdate_ScriptInfo Whose key is a_ScriptName in the FWUpdateMAP
OC_FWUpdate_ScriptInfo_c *     OC_ScriptInfo_c::GetFWUpdateObject
( OC_String_t a_ScriptName  )
{
  OC_FWUpdate_ScriptInfo_c * a_ReturnObject = NULL;
  OC_FWUpdateScriptsMap_t::iterator a_Iter;
  a_Iter = m_FWUpdateScriptsMap.find( a_ScriptName );
  if( a_Iter != m_FWUpdateScriptsMap.end() )
  {
    a_ReturnObject = (OC_FWUpdate_ScriptInfo_c *)a_Iter->second;
  }
  if( a_ReturnObject == NULL ) //.XX is not found in Map i.e, files are compressed, search for .XXg
  {
    if( a_ScriptName.at( a_ScriptName.size()-1) != 'g' )
    {
      a_ScriptName += "g";
      a_Iter = m_FWUpdateScriptsMap.find( a_ScriptName );
      if( a_Iter != m_FWUpdateScriptsMap.end() )
      {
        a_ReturnObject = (OC_FWUpdate_ScriptInfo_c *)a_Iter->second;
      }
    }
  }
  return a_ReturnObject;
}



//Returns an Object of OC_Test_ScriptInfo Whose key is a_ScriptName in the TestScriptMAP
OC_Test_ScriptInfo_c*         OC_ScriptInfo_c::GetTestObject
( OC_String_t a_ScriptName  )
{
  OC_Test_ScriptInfo_c * a_ReturnObject = NULL;
  OC_TestScriptsMap_t::iterator a_Iter;
  a_Iter = m_TestScriptsMap.find( a_ScriptName );
  if( a_Iter != m_TestScriptsMap.end() )
  {
    a_ReturnObject = (OC_Test_ScriptInfo_c*)a_Iter->second;
  }
  if( a_ReturnObject == NULL ) //.XX is not found in Map i.e, files are compressed, search for .XXg
  {
    if( a_ScriptName.at( a_ScriptName.size()-1) != 'g' )
    {
      a_ScriptName += "g";
      a_Iter = m_TestScriptsMap.find( a_ScriptName );
      if( a_Iter != m_TestScriptsMap.end() )
      {
        a_ReturnObject = (OC_Test_ScriptInfo_c*)a_Iter->second;
      }
    }
  }
  return a_ReturnObject;
}


//Returns an Object of OC_DataAcquisition_ScriptInfo Whose key is a_ScriptName in the DataAcquisitionScriptMAP
OC_DataAcquisition_ScriptInfo_c*      OC_ScriptInfo_c::GetDataAcqObject
( OC_String_t a_ScriptName  )
{
  OC_DataAcquisition_ScriptInfo_c * a_ReturnObject = NULL;
  OC_DataAcqScriptsMap_t::iterator a_Iter;

  a_Iter = m_DataAcquisitionScriptsMap.find( a_ScriptName );
  if( a_Iter != m_DataAcquisitionScriptsMap.end() )
  {
    a_ReturnObject = (OC_DataAcquisition_ScriptInfo_c*)a_Iter->second;
  }
  if( a_ReturnObject == NULL ) //.XX is not found in Map i.e, files are compressed, search for .XXg
  {
    if( a_ScriptName.at( a_ScriptName.size()-1) != 'g' )
    {
      a_ScriptName += "g";
      a_Iter = m_DataAcquisitionScriptsMap.find( a_ScriptName );
      if( a_Iter != m_DataAcquisitionScriptsMap.end() )
      {
        a_ReturnObject = (OC_DataAcquisition_ScriptInfo_c*)a_Iter->second;
      }
    }
  }
  return a_ReturnObject;
}


//Returns an Object of OC_Decode_ScriptInfo Whose key is a_ScriptName in the DecodeScriptInfoMap
OC_Decode_ScriptInfo_c*         OC_ScriptInfo_c::GetDecodeObject
( OC_String_t a_ScriptName  )
{
  OC_Decode_ScriptInfo_c*   a_ReturnObject = NULL;
  OC_DecodeScriptsMap_t::iterator a_Iter;
  a_Iter = m_DecodeScriptsMap.find( a_ScriptName );
  if( a_Iter != m_DecodeScriptsMap.end() )
  {
    a_ReturnObject = (OC_Decode_ScriptInfo_c*)a_Iter->second;
  }
  if( a_ReturnObject == NULL ) //.XX is not found in Map i.e, files are compressed, search for .XXg
  {
    if( a_ScriptName.at( a_ScriptName.size()-1) != 'g' )
    {
      a_ScriptName += "g";
      a_Iter = m_DecodeScriptsMap.find( a_ScriptName );
      if( a_Iter != m_DecodeScriptsMap.end() )
      {
        a_ReturnObject = (OC_Decode_ScriptInfo_c*)a_Iter->second;
      }
    }
  }
  return a_ReturnObject;
}


//Returns an Object of OC_Parse_ScriptInfo Whose key is a_ScriptName in the OC_Parse_ScriptInfoMAP
OC_Parse_ScriptInfo_c*          OC_ScriptInfo_c::GetParseObject
( OC_String_t a_ScriptName  )
{
  OC_Parse_ScriptInfo_c* a_ReturnObject = NULL;
  OC_ParseScriptsMap_t::iterator a_Iter;
  a_Iter = m_ParseScriptsMap.find( a_ScriptName );
  if( a_Iter != m_ParseScriptsMap.end() )
  {
    a_ReturnObject = (OC_Parse_ScriptInfo_c*)a_Iter->second;
  }
  if( a_ReturnObject == NULL ) //.XX is not found in Map i.e, files are compressed, search for .XXg
  {
    if( a_ScriptName.at( a_ScriptName.size()-1) != 'g' )
    {
      a_ScriptName += "g";
      a_Iter = m_ParseScriptsMap.find( a_ScriptName );
      if( a_Iter != m_ParseScriptsMap.end() )
      {
        a_ReturnObject = (OC_Parse_ScriptInfo_c*)a_Iter->second;
      }
    }
  }
  return a_ReturnObject;
}

//Returns Number representation of the Passed Argument;
OC_ULong_t OC_ScriptInfo_c::GetVersionAsNumber
( OC_String_t a_VersionString)
{
  OC_ULong_t    a_ReturnValue;
#ifdef OC_OS_OSF
	sscanf(a_VersionString.c_str(), "%lx", &a_ReturnValue);
#else
	a_ReturnValue = 0;
  sscanf(a_VersionString.c_str(), "%x", &a_ReturnValue);
#endif

  return a_ReturnValue;
}
//********************************************************************
//
// Class	:  OC_ScriptInfo_c
// Method	:
// Description	:
// Parameters	: <none>
// Returns	: <none>
// Comments	:
// Conditions:
// Should Return False if
// 1. The Script MetaData doesn't Exists in the DataBase.             (+)
// 2. RTE Version Mismatch with the Current tools Runtime Tool Verison. (+)
// 3. Broken Dependency Doesn't Met.                                  (+)

bool  OC_ScriptInfo_c::CheckDependency
( OC_String_t       a_ScriptName,
  OC_StringList_t&  a_DependencyListReference)
{
  //[Note:] a_ScriptName is of form [ <common\DependencyScriptName>:<MIN_VERSION> ]
  //OC_VERSION

  OC_String_t                       a_LocalScriptNameCopy             = a_ScriptName;
  OC_ULong_t                        a_ToolVersion                     = OC_VERSION  ; //Current tools RTEVERSION
  OC_Common_ScriptInfo_c *          a_TempObject                      = NULL;
  OC_Common_ScriptInfo_c *          a_LocalInstance                   = NULL;
  OC_StringList_t                   a_TmpDependencyList;
  OC_StringList_t                   a_TmpSubScriptsList;
  OC_StringList_t::iterator         a_Iter;
  OC_String_t                       a_TempString ;
  OC_ULong_t                        a_ScriptVersion;                  //Version of PresentScript
  OC_ULong_t                        a_RTEVersion;
  OC_ULong_t                        a_MinVersion;                     //Version of DependencyScript
  OC_String_t                       a_MinVersionString;
  bool                              a_FoundInDependencyListReference; //To remove the Duplicates in DependencyList
  bool                              a_DependencyMet                   = true;
  OC_ULong_t                        a_ColonPosition;                  //Colon position in the Dependency List.
  OC_String_t                       a_DevSpecScrName;                 // DriveSpecificScriptName for Library-Device Association.
  OC_ULong_t                        a_OpenBracePosition;              // Position of the "("
  OC_DataBase_c*                    a_pDataBase = NULL;
  OC_ScriptInfo_c*                  a_pScriptsObject = NULL;
  OC_String_t                       a_DeviceID;
  OC_String_t                       a_DepScriptName;


  if(a_ScriptName.find(":") == string::npos)
		g_FirstCall = true;
  //Seperating ScriptName and MIN_VERSION
  if( !g_FirstCall )
  {
    a_ColonPosition = a_ScriptName.find_first_of(":");
    a_MinVersionString = a_ScriptName.substr( a_ColonPosition + 1);
    a_ScriptName = a_ScriptName.substr(0, a_ColonPosition);
    a_MinVersion = GetVersionAsNumber( a_MinVersionString );
  }
  //Check for the a_scriptName in all the Maps
  //Get the Corresponding Object and call Dependencies
  //find Dependencies for all the Dependencies
  a_TempObject  = a_LocalInstance = GetObject( a_ScriptName );

  if( a_TempObject != NULL )                  // Existence Check Condition  1
  {
    a_RTEVersion = GetVersionAsNumber( a_TempObject->GetRTEVersion() );
    if(  a_RTEVersion > a_ToolVersion )  //RTEVersion Check Condition     2
    {
      //Script-Tool Version MisMatch
      OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg_P1(OC_MSGSET_SCRIPT_DATABASE,OC_MSG_SCRIPT_DATABASE_SCRIPT_TOOL_VERSION_ERROR,"ScriptName",a_ScriptName));
      a_DependencyListReference.clear();
      return false; //Dependency Not Met
    }
    else // ScriptVersion >= ToolVersion Which is Desired
    {
      // Then Check the remaining Dependencies for compatibility
      // Existence Met, RTEVERSION also MET
      // Check for BrokenVersion
      // Reading ScriptVersion
      if( g_FirstCall == false )
      {
        a_ScriptVersion = GetVersionAsNumber (  a_TempObject->GetScriptVersion()  );

        if( a_TempObject->GetBrokenVersion() != ""  ) //BRKVERSION Exists
        {
          OC_ULong_t a_BrokenVersion ;
          //Reading BrokenVersion
          a_BrokenVersion = GetVersionAsNumber( a_TempObject->GetBrokenVersion () );

          //if( (a_MinVersion >= a_BrokenVersion) && a_MinVersion <= a_ScriptVersion ) desired
          if( (a_MinVersion < a_BrokenVersion) || a_MinVersion > a_ScriptVersion )
          {
              //Broken Version Mismatch Error
              OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg_P1(OC_MSGSET_SCRIPT_DATABASE,OC_MSG_SCRIPT_DATABASE_BROKEN_VERSION_MISMATCH_ERROR,"ScriptName",a_ScriptName));
              a_DependencyListReference.clear(); //Clear ReturnVector
              return false; //Dependency Not Met
          }
        }
        else
        {
          //No broken version, but still need to check whether dependent version is as
          //expected..
          //if( a_MinVersion <= a_ScriptVersion ) desired
          if( a_MinVersion > a_ScriptVersion )
          {
              //Dependency Not Met
              OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg_P1(OC_MSGSET_SCRIPT_DATABASE,OC_MSG_SCRIPT_DATABASE_DEPENDENCY_NOT_MET_ERROR,"ScriptName",a_ScriptName));

              a_DependencyListReference.clear(); //Clear ReturnVector
              return false;
          }
        }
      }else
      {
        g_FirstCall = false;
      }

      a_TmpDependencyList = a_TempObject->GetDependencyList();
      for(  a_Iter = a_TmpDependencyList.begin() ; a_Iter != a_TmpDependencyList.end() ; a_Iter ++  )
      {
        //  Recursive Call here in a If...Else...
        //  *a_Iter == dir\ScriptName.pm:<MinVersion>(DEVASSOC1,DEVASSOC2,...) or Just dir\ScriptName.pm:<MinVersion>
        //  Eg: test/persScript.pm:0x04000000(nchikkamSDLT600,nchikkamSDLT320)
        a_DevSpecScrName    = *a_Iter;

        //check if the metadata had any ""
        if(a_DevSpecScrName.size() == 0)
          continue;

        a_OpenBracePosition = a_DevSpecScrName.find("(");
        if( a_OpenBracePosition == OC_String_t::npos ) //Not found
        {
          if (  CheckDependency( *a_Iter, a_DependencyListReference ) == false )
          {
            //Some dependency File Doesn't met the Criteria
            OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg_P1(OC_MSGSET_SCRIPT_DATABASE,OC_MSG_SCRIPT_DATABASE_DEPENDENCY_NOT_MET_ERROR,"ScriptName",a_ScriptName));
            a_DependencyListReference.clear(); //Clear ReturnVector
            return false;
          }
          else
          {
            // insert only if *a_Iter not present in the a_ReturnVector
            a_FoundInDependencyListReference = false;
            for(OC_StringList_t::iterator indexIter = a_DependencyListReference.begin(); indexIter!= a_DependencyListReference.end(); indexIter++)
            {
              a_TempString = (OC_String_t)*indexIter;
              OC_String_t       a_TempStr;
              a_TempStr = (OC_String_t)*a_Iter;
              a_ColonPosition = a_TempStr.find_first_of(":");
              a_ScriptName = a_TempStr.substr(0, a_ColonPosition);
              a_TempObject  = GetObject( a_ScriptName );

#ifdef OC_OS_OVMS
              if(g_StrCmpNoCase(a_TempObject->GetScriptName(), a_TempString) == true)
#else
              if(strcmp(a_TempObject->GetScriptName().c_str(), a_TempString.c_str()) == 0)
#endif
              {
                a_FoundInDependencyListReference = true;
                break;
              }
            }
            if( a_FoundInDependencyListReference == false )
            {
              OC_String_t       a_TempStr;
              a_TempStr = (OC_String_t)*a_Iter;
              a_ColonPosition = a_TempStr.find_first_of(":");
              a_ScriptName = a_TempStr.substr(0, a_ColonPosition);
              a_TempObject  = GetObject( a_ScriptName );
              a_DependencyListReference.push_back ( a_TempObject->GetScriptName() );
            }
          }
        }//"(" Not Found in the List.
        else //"(" Found in the string
        {
          // Pass the Same ScriptName for Different DeviceAssociation List.
          // Steps:
          // 1. Populate the DeviceAssociation List.
          // 2. Call the CheckDependency(DevAssicList[index]) for the Script In Hand.
          OC_StringList_t a_DevAssocList;
          OC_ULong_t      a_CommaPos;
          OC_String_t     a_DebugStr;
          a_OpenBracePosition = a_DevSpecScrName.find("(");
          a_DepScriptName = a_DevSpecScrName.substr(  0, a_OpenBracePosition  );
          a_DebugStr = a_DevSpecScrName.substr(a_OpenBracePosition+1);
          a_CommaPos = a_DebugStr.find(",");
          while( a_CommaPos != string::npos )
          {
            a_DevAssocList.push_back(a_DebugStr.substr(0, a_CommaPos) );
            a_DebugStr = a_DebugStr.substr(a_CommaPos+1);
            a_CommaPos = a_DebugStr.find(",");
          }
          a_CommaPos = a_DebugStr.find(")");
          a_DebugStr = a_DebugStr.substr(0, a_CommaPos);
          a_DevAssocList.push_back( a_DebugStr  );

          for ( OC_ULong_t a_TInd = 0; a_TInd != a_DevAssocList.size(); a_TInd++ )
          {
            //a_DeviceID      = a_DevSpecScrName.substr(a_OpenBracePosition+1, (strlen(a_DevSpecScrName.c_str())-a_OpenBracePosition)-2);
            a_DeviceID      = a_DevAssocList.at(a_TInd);

            a_pDataBase = OC_PlatformFactory_c::m_pCurrent->Get_DataBase();
            a_pScriptsObject = a_pDataBase->GetScriptInfo(a_DeviceID);
            if( a_pScriptsObject == NULL )
            {
              //Script itself doesn't exists in the DataBase, Invalid Reference Error!
              OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg_P1(OC_MSGSET_SCRIPT_DATABASE,OC_MSG_SCRIPT_DATABASE_INVALID_SCRIPT_REFERENCE_ERROR,"ScriptName",a_DepScriptName));

              a_DependencyListReference.clear();
              return false;
            }
            else
            {
              if( a_pScriptsObject->CheckDependency( a_DepScriptName, a_DependencyListReference) == false )
              {
                //Some dependency File Doesn't met the Criteria
                OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg_P1(OC_MSGSET_SCRIPT_DATABASE,OC_MSG_SCRIPT_DATABASE_DEPENDENCY_NOT_MET_ERROR,"ScriptName",a_DepScriptName));
                a_DependencyListReference.clear();
                return false;
              }
            }
          }//For all the DeviceAssociation Of the Script...
          OC_String_t       a_TempStr;
          a_TempStr = a_DepScriptName;
          a_ColonPosition = a_TempStr.find_first_of(":");
          a_ScriptName = a_TempStr.substr(0, a_ColonPosition);
          a_TempObject  = a_pScriptsObject->GetObject( a_ScriptName );
          a_DependencyListReference.push_back(a_TempObject->GetScriptName());
        }// For All (DEVASSOC1,DEVASSOC2,...)
      }//for all the dependent Scripts

      a_TmpSubScriptsList = a_LocalInstance->GetSubScriptsList();
      for(  a_Iter = a_TmpSubScriptsList.begin() ; a_Iter != a_TmpSubScriptsList.end() ; a_Iter ++  )
      {
        //Recursive Call here in a If...Else...
        if (  CheckDependency( *a_Iter, a_DependencyListReference ) == false )
        {
          //Some dependency File Doesn't met the Criteria
          OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg_P1(OC_MSGSET_SCRIPT_DATABASE,OC_MSG_SCRIPT_DATABASE_DEPENDENCY_NOT_MET_ERROR,"ScriptName",a_ScriptName));
          a_DependencyListReference.clear(); //Clear ReturnVector
          return false;
        }
        else
        {
          // insert only if *a_Iter not present in the a_ReturnVector
          a_FoundInDependencyListReference = false;
          for(OC_StringList_t::iterator indexIter = a_DependencyListReference.begin(); indexIter!= a_DependencyListReference.end(); indexIter++)
          {
            a_TempString = (OC_String_t)*indexIter;
            OC_String_t       a_TempStr;
            a_TempStr = (OC_String_t)*a_Iter;
            a_ColonPosition = a_TempStr.find_first_of(":");
            a_ScriptName = a_TempStr.substr(0, a_ColonPosition);
            a_TempObject  = GetObject( a_ScriptName );

#ifdef OC_OS_OVMS
              if(g_StrCmpNoCase(a_TempObject->GetScriptName(), a_TempString) == true)
#else
            if(strcmp(a_TempObject->GetScriptName().c_str(), a_TempString.c_str()) == 0)
#endif
            {
              a_FoundInDependencyListReference = true;
              break;
            }
          }
          if( a_FoundInDependencyListReference == false )
          {
            OC_String_t       a_TempStr;
            a_TempStr = (OC_String_t)*a_Iter;
            a_ColonPosition = a_TempStr.find_first_of(":");
            a_ScriptName = a_TempStr.substr(0, a_ColonPosition);
            a_TempObject  = GetObject( a_ScriptName );
            a_DependencyListReference.push_back ( a_TempObject->GetScriptName() );
          }
        }
      }//for all the dependent Scripts
    }//Script Version
  }// Script Exists in the Index-DataBase
  else
  {
    //Script itself doesn't exists in the DataBase, Invalid Reference Error!
    OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg_P1(OC_MSGSET_SCRIPT_DATABASE,OC_MSG_SCRIPT_DATABASE_INVALID_SCRIPT_REFERENCE_ERROR,"ScriptName",a_ScriptName));

    a_DependencyListReference.clear();
    a_DependencyMet = false;
  }
  if( a_LocalScriptNameCopy.find(":") == string::npos )
  {
    // This function returns only the list of dependent scripts excluding the initially passed one.
    // Since this block will be executed only for the initial call stack, the initially passed argument
    // can be pushed into the reference vector.//ToDo.[Optional]
    // a_ColonPosition = a_ScriptName.find_first_of(":");
    // a_MinVersionString = a_ScriptName.substr( a_ColonPosition + 1);
    // a_ScriptName = a_ScriptName.substr(0, a_ColonPosition);
    // a_DependencyListReference.push_back (a_ScriptName);
    g_FirstCall = true;
  }
  return a_DependencyMet;
}

//********************************************************************
//
// Class	:         OC_DataBase_c
// Method	:
// Description	:
// Parameters	: <none>
// Returns	: <none>
// Comments	:

OC_DataBase_c::OC_DataBase_c
(  void   ) :g_lszCommonScriptsKey("COMMON")
{
}

OC_DataBase_c::~OC_DataBase_c
(  void  )
{
  DeallocateMaps();
}


bool  OC_DataBase_c::Initialize
(   void )
{
  try
  {

#if defined(OC_OS_OVMS)
    TraverseDirectories ( g_BuildPath(OC_PlatformFactory_c::m_pCurrent->Config_GetStringValue("Root Directory"), OC_IMMSTRING("SCRIPTS"), true) );
#elif defined(OC_OS_NW)
    TraverseDirectories ( "sys:\\system\\nchikkam_tools\\scripts" );
#else
    TraverseDirectories ( g_BuildPath(OC_PlatformFactory_c::m_pCurrent->Config_GetStringValue("Root Directory"), OC_IMMSTRING("scripts")) );
#endif
    return true;
  }
  catch(...)
  {
    //display a dialog box nad return false..
    return false;
  }
}

OC_ScriptInfo_c* OC_DataBase_c::GetScriptInfo
( OC_String_t a_Key )
{
  OC_ScriptInfoMap_t::iterator a_Iter;
  a_Iter = m_DataBase.find(a_Key);
  if( a_Iter != m_DataBase.end() )
  {
    //Found
    return a_Iter->second;
  }
  return NULL;
}
//********************************************************************
//
// Class	:
// Method	:
// Description	:
// Parameters	: <none>
// Returns	: <none>
// Comments	:
//Traverses the Directories recursively and Constructs the Index DataBase.
//On Creating an Object for a Script X, This function calls UpdateMap(X) for
//Updating the DataBase.
void OC_DataBase_c::TraverseDirectories
(OC_String_t   a_RootDirectory,
 OC_Long_t a_ActualScriptType )
{
  //[Note:]We have to traverse the directory contents and if entries are file then do the
  //processing, but if entry is directory call the this function recrsively with that entry
  //as parameter..
  const  OC_Long_t                        a_UnknownScriptType = -1;
  OC_Long_t                               a_ScriptType = a_UnknownScriptType;
  bool                                    a_IsDirectory             = false;
#if defined (OC_OS_WINDOWS) || defined (OC_OS_NW)
  OC_String_t                             a_Mask                    = OC_IMMSTRING("*.*");
#elif defined (OC_OS_UNIX)
  OC_String_t                             a_Mask                    = OC_IMMSTRING("");
#endif
  OC_String_t                             a_Folder;
  OC_String_t                             a_Filename;
  OC_PlatformFactory_c::OC_DirHandle_t    a_Handle;
  OC_String_t                             a_ParentDirectory;
#ifdef OC_OS_OVMS
  OC_String_t				                      a_DirName;
  OC_String_t				                      a_ParentDirName;
  OC_String_t				                      a_FileExtn;
#endif

  a_Folder = a_RootDirectory;
   a_Handle= OC_PlatformFactory_c::m_pCurrent->File_InitDirSearch(a_Folder,a_Mask);
   if(!a_Handle)
   {
     //publish event log saying that passed directory doesn't exist..
     //Do we need to throw excpetion here....
     //If it is unable to find one directory...then script execution part might
     //fail completely..
#if defined(OC_OS_WINDOWS)
     OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg_P2(OC_MSGSET_SCRIPT_DIRECTORY_HIERARCHY,OC_MSG_SCRIPT_DIRECTORY_HIERARCHY_DIR_OPEN_ERROR,"Filename", a_Folder, "ErrorNum", GetLastError()));
#else
     OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg_P2(OC_MSGSET_SCRIPT_DIRECTORY_HIERARCHY,OC_MSG_SCRIPT_DIRECTORY_HIERARCHY_DIR_OPEN_ERROR,"Filename", a_Folder, "ErrorNum", errno));
#endif

   }
   else
   {

     //Directory exist..
     while(OC_PlatformFactory_c::m_pCurrent->File_GetNextFile(a_Handle,a_Filename) == true)
     {
       //If the entries are "." and ".." just ignore them
       a_ParentDirectory = a_Filename.substr( a_Filename.size() -1);

       if(strcmp(a_ParentDirectory.c_str(), OC_IMMSTRING(".").c_str()) == 0 || strcmp(a_ParentDirectory.c_str(), OC_IMMSTRING("..").c_str()) == 0)
        continue;
       //Here we need to handle operating system specific things..for knowing whether the
       //entry is directory or NOT....

#if defined(OC_OS_WINDOWS)
       //[Note:] Modified Here
         struct _stat               a_FileInfo;

         _stat(a_Filename.c_str(), &a_FileInfo); //returns 0 on Success
         if(a_FileInfo.st_mode & _S_IFDIR)
          a_IsDirectory = true;
         else
          a_IsDirectory = false;
#else
         struct stat                 a_FileInfo;
         stat(a_Filename.c_str(),&a_FileInfo);
         if(a_FileInfo.st_mode & S_IFDIR)
          a_IsDirectory = true;
         else
          a_IsDirectory = false;
#endif
         if(a_IsDirectory)
         {

           //Recursive Call to iterate all the files in the subfolders before
           //Traversing all the files in present directory;
           if( a_ActualScriptType == -1 ) //This will be -1 for all the Folders in Passed Directory
           {
              a_ScriptType = GetScriptType(a_Filename);
           }
           else
           {  // The directory found is a strange one eg:common\perl so all the scripts
              // in perl will be of type common, so modify the a_ScriptType and pass it
              // for the subsequent Calls.
              a_ScriptType = a_ActualScriptType;
           }
#ifdef OC_OS_OVMS
	         // Now we know that it is directory by stat function...
           // separate out the filename from directory, the filename is
	         // complete path, so if it is a directory then we need form
           // filename properly that is valid for OVMS beacuse it distiguish
           // in representation of regular file and directory..
           a_DirName = a_Filename.substr((a_Filename.find_last_of(OC_CHAR(']'))+1), (a_Filename.find_last_of(OC_CHAR('.'))));
           a_DirName = a_DirName.substr(0, a_DirName.find_last_of(OC_CHAR('.')));
           a_ParentDirName = a_Filename.substr(0, a_Filename.find_last_of(OC_CHAR(']'))+1);
           a_Filename = g_BuildPath(a_ParentDirName, a_DirName, true);
#endif
           TraverseDirectories ( a_Filename, a_ScriptType  );
         }
         else
         {
           //File is not a directory...and check for supported script
           if(  a_Filename.find(".pl") != string::npos ||
                a_Filename.find(".pm") != string::npos ||
                a_Filename.find(".plg") != string::npos ||
                a_Filename.find(".pmg") != string::npos ||
                a_Filename.find(".PL") != string::npos ||
                a_Filename.find(".PM") != string::npos ||
                a_Filename.find(".PLG") != string::npos ||
                a_Filename.find(".PMG") != string::npos  )
           { // (Compressed/UnCompressed)File is either a Perl Module of a Perl Script
             //check for script type and then update the metadata object for that script...
             InsertEntry(a_Filename, a_ActualScriptType);
           } //If file is not directory....
         } //Supported Script
     }//If there is an entry in the directory
     OC_PlatformFactory_c::m_pCurrent->File_ExitDirSearch(a_Handle);
   } //If the directory exist...
}//TraverseDirectories();





//********************************************************************
//
// Class	:
// Method	:
// Description	:
// Parameters	: <none>
// Returns	: <none>
// Comments	:
//           This function checks whether the a_metaDataObject's
//           DeviceAssociation is present in the DataBase, if yes
//           it updates the Corresponding Object if not, it just
//           adds an entry in to the DataBase;
// Basic Steps:
// Search for the Device Association Key In MAP
// if (found)
//     UpdateThe Value Object in the Map
// else
//     Add an entry to the MAP

void  OC_DataBase_c::UpdateMap
( OC_Common_ScriptInfo_c* a_MetaDataObject )
{
  OC_ScriptInfo_c*                   a_NewObjectAllocationPtr       = NULL;
  OC_String_t                        a_DeviceAssociationKey;
  OC_StringList_t::iterator          a_IndexIter;
  OC_StringList_t                    a_DeviceAssociationList;
  OC_ScriptInfoMap_t::iterator       a_Iter ;
  OC_String_t                        a_ScriptType;
  a_ScriptType = a_MetaDataObject->GetScriptType();
  bool                               a_FirstEntry = false;
  //Converting a_ScriptType to lowercase for comparision;
  std::transform( a_ScriptType.begin(),
                 a_ScriptType.end(),
                 a_ScriptType.begin(),
                 tolower);

  if( a_ScriptType == "common")  //GetDeviceAssocList() doesn't Exists for CommonScripts;
  { //Search for Key "COMMON"
    a_Iter = m_DataBase.find( g_lszCommonScriptsKey );
    if( a_Iter != m_DataBase.end() )
    {  //Found in the DataBase. Update the Pointer
       a_NewObjectAllocationPtr = a_Iter->second;
       OC_CommonScriptsMap_t&  a_commonScriptsMap = a_NewObjectAllocationPtr->CommonScriptsMapReference();
       a_commonScriptsMap[ a_MetaDataObject->GetScriptName() ] = a_MetaDataObject;

    }
    else
    {  //Not found, Instantiate a MainObject and store it with key "COMMON";
       a_NewObjectAllocationPtr = new OC_ScriptInfo_c();
       OC_CommonScriptsMap_t&  a_commonScriptsMap = a_NewObjectAllocationPtr->CommonScriptsMapReference();
       a_commonScriptsMap[ a_MetaDataObject->GetScriptName() ] = a_MetaDataObject;
       m_DataBase [ g_lszCommonScriptsKey ] = a_NewObjectAllocationPtr;
    }
  }
  else
  {
    a_DeviceAssociationList = a_MetaDataObject->GetDeviceAssociationList();
    if( a_DeviceAssociationList.size() == 0 ) //Is a Sub Script;
    { //Both common scripts and Sub scripts can be accessed with g_lszCommonScriptsKey
      a_Iter = m_DataBase.find( g_lszCommonScriptsKey );
      if( a_Iter != m_DataBase.end() )
      {  //Found in the DataBase. Update the Pointer
         a_NewObjectAllocationPtr = a_Iter->second;
         OC_SubScriptsMap_t&  a_SubScriptsMap = a_NewObjectAllocationPtr->SubScriptsMapReference();
         a_SubScriptsMap[ a_MetaDataObject->GetScriptName() ] = a_MetaDataObject;
      }
      else
      {  //Not found, Instantiate a MainObject and store it with key "COMMON";
         a_NewObjectAllocationPtr = new OC_ScriptInfo_c();
         OC_SubScriptsMap_t&  a_SubScriptsMap = a_NewObjectAllocationPtr->SubScriptsMapReference();
         a_SubScriptsMap[ a_MetaDataObject->GetScriptName() ] = a_MetaDataObject;
         m_DataBase [ g_lszCommonScriptsKey ] = a_NewObjectAllocationPtr;
      }
    }// Helper Script
    else
    { //Script Object is Device Specific.
      for ( a_IndexIter = a_DeviceAssociationList.begin(); a_IndexIter != a_DeviceAssociationList.end(); a_IndexIter ++)
      {
        a_DeviceAssociationKey = (OC_String_t)(*a_IndexIter) ;
        if( a_ScriptType == "dataacq" )
        {
          a_Iter = m_DataBase.find( a_DeviceAssociationKey );
          if ( a_Iter != m_DataBase.end() )
          {//Found in DataBase
             OC_ScriptInfo_c* & a_ref = a_Iter->second;
             OC_DataAcqScriptsMap_t & dataAcqMap = a_ref->DataAcqScriptsMapReference();
             dataAcqMap[ a_MetaDataObject->GetScriptName() ] = a_MetaDataObject;
          }
          else
          {//Not Found in the DataBase;
              a_NewObjectAllocationPtr = new OC_ScriptInfo_c();
              OC_DataAcqScriptsMap_t & dataAcqMap = a_NewObjectAllocationPtr->DataAcqScriptsMapReference();
              dataAcqMap[  a_MetaDataObject->GetScriptName() ] = a_MetaDataObject;
              m_DataBase[ a_DeviceAssociationKey ]   = a_NewObjectAllocationPtr;
          }
        }//Not a  DataAcqObject
        else
          if ( a_ScriptType == "decode" )
        {
          a_Iter = m_DataBase.find( a_DeviceAssociationKey );
          if ( a_Iter != m_DataBase.end() )
          {//Found : Update
             OC_ScriptInfo_c* & a_ref = a_Iter->second;
             //Add An Entry to the Inner-Map.
             OC_DecodeScriptsMap_t & decodeScriptsMap = a_ref->DecodeScriptsMapReference();
             decodeScriptsMap[ a_MetaDataObject->GetScriptName() ] = a_MetaDataObject ;
          }
          else
          {
              a_NewObjectAllocationPtr = new OC_ScriptInfo_c();
              OC_DecodeScriptsMap_t & decodeScripsMap = a_NewObjectAllocationPtr->DecodeScriptsMapReference();
              decodeScripsMap[  a_MetaDataObject->GetScriptName() ] = a_MetaDataObject ;
              m_DataBase[ a_DeviceAssociationKey ]   = a_NewObjectAllocationPtr ;
          }
        }
        else //Not a Decode Object
          if ( a_ScriptType == "parse" )
        {
          a_Iter = m_DataBase.find( a_DeviceAssociationKey );
          if ( a_Iter != m_DataBase.end() )
          { //Found : Update
            OC_ScriptInfo_c* & a_ref = a_Iter->second;
            //Add An Entry to the Inner-Map.
            OC_ParseScriptsMap_t & parseScriptsMap = a_ref->ParseScriptsMapReference();
            parseScriptsMap[ a_MetaDataObject->GetScriptName() ] = a_MetaDataObject;
          }
          else
          { //Not Found : Insert a new Entry
            a_NewObjectAllocationPtr = new OC_ScriptInfo_c();
            OC_ParseScriptsMap_t & parseScriptsMap = a_NewObjectAllocationPtr->ParseScriptsMapReference();
            parseScriptsMap[  a_MetaDataObject->GetScriptName() ] = a_MetaDataObject;
            m_DataBase[ a_DeviceAssociationKey ]   = a_NewObjectAllocationPtr ;
          }
        }
        else //Not a ParseObject
          if ( a_ScriptType == "sticket" )
        {
          a_Iter = m_DataBase.find( a_DeviceAssociationKey );
          if ( a_Iter != m_DataBase.end() )
          {//Found : Update
            OC_ScriptInfo_c* & a_ref = a_Iter->second;
            OC_STicketScriptsMap_t & sticketMap = a_ref->STicketScriptsMapReference();
            sticketMap[ a_MetaDataObject->GetScriptName() ] = a_MetaDataObject;
          }
          else
          {
            a_NewObjectAllocationPtr = new OC_ScriptInfo_c();
            OC_STicketScriptsMap_t & dataAcqMap = a_NewObjectAllocationPtr->STicketScriptsMapReference();
            dataAcqMap[  a_MetaDataObject->GetScriptName() ] = a_MetaDataObject;
            m_DataBase[ a_DeviceAssociationKey ]   = a_NewObjectAllocationPtr;
          }
        }
        else //Not a STicketObject
          if ( a_ScriptType == "fwupdate" )
        {
          a_Iter = m_DataBase.find( a_DeviceAssociationKey );
          if ( a_Iter != m_DataBase.end() )
          { //Found : Update
            OC_ScriptInfo_c* & a_ref = a_Iter->second;
            //Add An Entry to the Inner-Map.
            OC_FWUpdateScriptsMap_t & fwUpdateScriptsMap = a_ref->FWUpdateScriptsMapReference();
            fwUpdateScriptsMap[ a_MetaDataObject->GetScriptName() ] = a_MetaDataObject;
          }
          else
          { //Not Found : Insert a new Entry
            a_NewObjectAllocationPtr = new OC_ScriptInfo_c();
            OC_FWUpdateScriptsMap_t & fwUpdateScriptsMap = a_NewObjectAllocationPtr->FWUpdateScriptsMapReference();
            fwUpdateScriptsMap[  a_MetaDataObject->GetScriptName() ] = a_MetaDataObject;
            m_DataBase[ a_DeviceAssociationKey ]   = a_NewObjectAllocationPtr ;
            }
        }
        else //Not a TestScriptObject
          if ( a_ScriptType == "test" )
        {
          a_Iter = m_DataBase.find( a_DeviceAssociationKey );
          if ( a_Iter != m_DataBase.end() )
          { //Found : Update
            OC_ScriptInfo_c* & a_ref = a_Iter->second;
            //Add An Entry to the Inner-Map.
            OC_TestScriptsMap_t & testScriptsMap = a_ref->TestScriptsMapReference();
            testScriptsMap[ a_MetaDataObject->GetScriptName() ] = a_MetaDataObject;
          }
          else
          { //Not Found : Insert a new Entry
            a_NewObjectAllocationPtr = new OC_ScriptInfo_c();
            OC_TestScriptsMap_t & testScriptsMap = a_NewObjectAllocationPtr->TestScriptsMapReference();
            testScriptsMap[  a_MetaDataObject->GetScriptName() ] = a_MetaDataObject;
            m_DataBase[ a_DeviceAssociationKey ]   = a_NewObjectAllocationPtr ;
          }
        }//TestScriptType
      }  //For All the DeviceAssociations
    }//Device Specific
  }//If()..Else () not a CommonScript;
}


// Comments:      Determines the type of the script and returns an integer
//                representation

OC_Long_t OC_DataBase_c::GetScriptType
( OC_String_t a_Path)
{
  const OC_ULong_t      a_FoldersCount = 7;
  OC_String_t a_Folders[a_FoldersCount] = {
                              "common",  //0
                              "dataacq", //1 ...
                              "decode",
                              "parse",
                              "sticket",
                              "fwupdate"  ,
                              "test"
                            };
  OC_String_t a_CapsFolders[a_FoldersCount] = {
                              "COMMON",  //0
                              "DATAACQ", //1 ...
                              "DECODE",
                              "PARSE",
                              "STICKET",
                              "FWUPDATE"  ,
                              "TEST"
                            };

  OC_Long_t   a_ReturnValue = -1;
  OC_Long_t  a_Position;
  OC_String_t a_FolderName;
  OC_String_t a_DirectorySeperator;
  OC_ULong_t  a_Index;
  a_DirectorySeperator = OC_PlatformFactory_c::m_pCurrent->FName_GetSeparator();
  #ifdef OC_OS_OVMS
  a_FolderName = a_Path.substr(a_Path.find_last_of(OC_CHAR(']'))+1, a_Path.find_last_of(OC_CHAR('.')));
  a_FolderName = a_FolderName.substr(0, a_FolderName.find_last_of(OC_CHAR('.')));
#else
  a_Position = a_Path.find_last_of( a_DirectorySeperator  );
  a_FolderName = a_Path.substr ( a_Position + 1 );
#endif
  for ( a_Index = 0 ; a_Index < a_FoldersCount ; a_Index ++)
  {
    if ( strcmp(a_FolderName.c_str(), a_Folders[a_Index].c_str()) == 0 || strcmp(a_FolderName.c_str(), a_CapsFolders[a_Index].c_str()) == 0)
    {
      a_ReturnValue = a_Index;
      break;
    }
  }
  return a_ReturnValue;
}


//********************************************************************
//
// Class	:         OC_DataBase_c
// Method	:         DeallocateMaps
// Parameters	:     <none>
// Returns	:       <none>
// Comments	:       Makes use of an intermediate Map (ReferenceCounting Map)to deallocate the
//                  ScriptObjects:-
//                  m_ScriptsMap<ScriptName, DevAssocList[0]> : This map maintains the List
//                  of all the Scripts and FirstDevAssoc of every Script. This is to make sure
//                  that the Memory allocated for a Script(ScriptObject), Will be deallocated
//                  Properly.
//
void OC_DataBase_c::DeallocateMaps()
{
  OC_ScriptInfoMap_t::iterator  a_Iter;
  OC_String_t                   a_DeviceKey;
  OC_ScriptInfo_c*              a_pScriptInfo;
  OC_String_t                   a_ScriptName;
  OC_ScriptMap_t::iterator      a_LookupIter;
  OC_CommonScriptsMap_t::iterator a_CommonIter;

  //CommonScripts Map and SubScripts Map are Class Variable(Static, So deallocation of these Maps
  //Should be handled seperately
  a_Iter = m_DataBase.find( g_lszCommonScriptsKey );
  if ( a_Iter != m_DataBase.end() )
  {
    a_pScriptInfo = a_Iter->second;
    OC_CommonScriptsMap_t& a_CommonMap = a_pScriptInfo->CommonScriptsMapReference();
    for ( a_CommonIter = a_CommonMap.begin(); a_CommonIter != a_CommonMap.end(); a_CommonIter ++ )
    {
      a_LookupIter = m_ScriptsMap.find(a_CommonIter->first);
      if(a_LookupIter != m_ScriptsMap.end())
      {
        if( strcmp(a_LookupIter->second.c_str(), g_lszCommonScriptsKey.c_str() ) == 0 )
        {
          delete a_CommonIter->second;
        }
      }
    }
    a_CommonMap.clear();
    //Deallocate the SubScripts(Helper) Map also
    OC_SubScriptsMap_t& a_SubScriptsMap = a_pScriptInfo->SubScriptsMapReference();
    for ( a_CommonIter = a_SubScriptsMap.begin(); a_CommonIter != a_SubScriptsMap.end(); a_CommonIter ++ )
    {
      a_LookupIter = m_ScriptsMap.find(a_CommonIter->first);
      if(a_LookupIter != m_ScriptsMap.end())
      {
        if( strcmp(a_LookupIter->second.c_str(), g_lszCommonScriptsKey.c_str() ) == 0 )
        {
          delete a_CommonIter->second;
        }
      }
    }
    a_SubScriptsMap.clear();
  }
  //Clean up all the Other maps in each ScriptInfo_c Object.
  for ( a_Iter = m_DataBase.begin(); a_Iter != m_DataBase.end(); a_Iter ++)
  {
    a_DeviceKey = a_Iter->first;
    if( strcmp(a_DeviceKey.c_str(), g_lszCommonScriptsKey.c_str() ) == 0 )   //Skip (COMMON) DeviceAssociation.
        continue;
    a_pScriptInfo = a_Iter->second;

    OC_STicketScriptsMap_t& a_STicketMap = a_pScriptInfo->STicketScriptsMapReference();
    for ( a_CommonIter = a_STicketMap.begin(); a_CommonIter != a_STicketMap.end(); a_CommonIter ++)
    {
      a_LookupIter = m_ScriptsMap.find(a_CommonIter->first);
      if(a_LookupIter != m_ScriptsMap.end())
      {
        if( strcmp(a_LookupIter->second.c_str(), a_DeviceKey.c_str()) == 0 )
        {
          delete a_CommonIter->second;
        }
      }
    }
    a_STicketMap.clear();

    OC_FWUpdateScriptsMap_t& a_FWUpdateMap = a_pScriptInfo->FWUpdateScriptsMapReference();
    for ( a_CommonIter = a_FWUpdateMap.begin(); a_CommonIter != a_FWUpdateMap.end(); a_CommonIter ++)
    {
      a_LookupIter = m_ScriptsMap.find(a_CommonIter->first);
      if(a_LookupIter != m_ScriptsMap.end())
      {
        if( strcmp(a_LookupIter->second.c_str(), a_DeviceKey.c_str()) == 0 )
        {
          delete a_CommonIter->second;
        }
      }
    }
    a_FWUpdateMap.clear();

    OC_TestScriptsMap_t& a_TestScriptsMap = a_pScriptInfo->TestScriptsMapReference();
    for ( a_CommonIter = a_TestScriptsMap.begin(); a_CommonIter != a_TestScriptsMap.end(); a_CommonIter ++)
    {
      a_LookupIter = m_ScriptsMap.find(a_CommonIter->first);
      if(a_LookupIter != m_ScriptsMap.end())
      {
        if( strcmp(a_LookupIter->second.c_str(), a_DeviceKey.c_str()) == 0 )
        {
          delete a_CommonIter->second;
        }
      }
    }
    a_TestScriptsMap.clear();

    OC_DataAcqScriptsMap_t& a_DataAcqMap = a_pScriptInfo->DataAcqScriptsMapReference();
    for ( a_CommonIter = a_DataAcqMap.begin(); a_CommonIter != a_DataAcqMap.end(); a_CommonIter ++)
    {
      a_LookupIter = m_ScriptsMap.find(a_CommonIter->first);
      if(a_LookupIter != m_ScriptsMap.end())
      {
        if( strcmp(a_LookupIter->second.c_str(), a_DeviceKey.c_str()) == 0 )
        {
          delete a_CommonIter->second;
        }
      }
    }
    a_DataAcqMap.clear();

    OC_DecodeScriptsMap_t& a_DecodeMap = a_pScriptInfo->DecodeScriptsMapReference();
    for ( a_CommonIter = a_DecodeMap.begin(); a_CommonIter != a_DecodeMap.end(); a_CommonIter ++)
    {
      a_LookupIter = m_ScriptsMap.find(a_CommonIter->first);
      if(a_LookupIter != m_ScriptsMap.end())
      {
        if( strcmp(a_LookupIter->second.c_str(), a_DeviceKey.c_str()) == 0 )
        {
          delete a_CommonIter->second;
        }
      }
    }
    a_DecodeMap.clear();

    OC_ParseScriptsMap_t& a_ParseMap = a_pScriptInfo->ParseScriptsMapReference();
    for ( a_CommonIter = a_ParseMap.begin(); a_CommonIter != a_ParseMap.end(); a_CommonIter ++)
    {
      a_LookupIter = m_ScriptsMap.find(a_CommonIter->first);
      if(a_LookupIter != m_ScriptsMap.end())
      {
        if( strcmp(a_LookupIter->second.c_str(), a_DeviceKey.c_str()) == 0 )
        {
          delete a_CommonIter->second;
        }
      }
    }
    a_ParseMap.clear();
  }
  m_ScriptsMap.clear();
}

//********************************************************************
//
// Class	:       OC_DataBase_c
// Method	:       InsertEntry
// Description	: Instantiates a Specific Script Type object and Fills the
//                Fields with the related Information.
// Parameters	:   a_Filename
// Returns	:     a_ActualScriptType
// Comments	:     Calls the method UpdateMap() to insert an Entry in to the DataBase.
void OC_DataBase_c::InsertEntry(OC_String_t a_Filename, OC_Long_t a_ActualScriptType)
{
 OC_Common_ScriptInfo_c*                 a_CommonMetaObjectAutoPtr;
 const  OC_Long_t                        a_UnknownScriptType = -1;

 if( a_ActualScriptType != a_UnknownScriptType )
 {
   switch( a_ActualScriptType  )
   {
     case OC_Scripts_DataAcq_e:
               a_CommonMetaObjectAutoPtr = new OC_DataAcquisition_ScriptInfo_c();
               break;
    case OC_Scripts_Common_e:
               a_CommonMetaObjectAutoPtr = new OC_Common_ScriptInfo_c();
               break;
    case OC_Scripts_STicket_e:
               a_CommonMetaObjectAutoPtr = new OC_STicket_ScriptInfo_c();
               break;
    case OC_Scripts_Decode_e:
               a_CommonMetaObjectAutoPtr = new OC_Decode_ScriptInfo_c();
               break;
    case OC_Scripts_Parse_e:
               a_CommonMetaObjectAutoPtr = new OC_Parse_ScriptInfo_c();
               break;
    case OC_Scripts_FWUpdate_e:
               a_CommonMetaObjectAutoPtr = new OC_FWUpdate_ScriptInfo_c();
               break;
    case OC_Scripts_Test_e:
               a_CommonMetaObjectAutoPtr = new OC_Test_ScriptInfo_c();
               break;
   }
  }

  if(a_CommonMetaObjectAutoPtr == NULL)
  {
    return;
  }
  //ReadMetaDataIs Virtual Function;
  a_CommonMetaObjectAutoPtr->ReadMetaData(a_Filename);
  if((strcmp(a_CommonMetaObjectAutoPtr->GetScriptType().c_str(), "common" )== 0) || (strcmp(a_CommonMetaObjectAutoPtr->GetScriptType().c_str(), "COMMON" )== 0))
    m_ScriptsMap.insert(OC_ScriptMap_t::value_type(a_CommonMetaObjectAutoPtr->GetScriptName(), g_lszCommonScriptsKey));
  else
  {
    OC_StringList_t& a_DevList = a_CommonMetaObjectAutoPtr->GetDeviceAssociationList();
    if(a_DevList.size())
      m_ScriptsMap.insert(OC_ScriptMap_t::value_type(a_CommonMetaObjectAutoPtr->GetScriptName(), a_DevList.at(0)));
    else
    {
      m_ScriptsMap.insert(OC_ScriptMap_t::value_type(a_CommonMetaObjectAutoPtr->GetScriptName(), g_lszCommonScriptsKey));
    }
  }
  UpdateMap(a_CommonMetaObjectAutoPtr);
}

//********************************************************************
//
// Class	:               OC_DataBase_c
// Method	:               Refresh(void)
// Description	:         Deallocates the Memory That was allocated for DataBase Maps
//                        and Reconstructs the Maps.
// Parameters	: <none>
// Returns	:   <none>
// Comments	:             Calls the methods DeallocateMaps(), and Initialize()
void OC_DataBase_c::Refresh()
{
  DeallocateMaps();
  Initialize();
}


//********************************************************************
//
// Class:             OC_DataBase_c
// Method:            RemoveEntry
// Description:       Removes an object from the DataBase.
// Parameters	:       a_DeviceID          ---     VendorID + ProductID
//                    a_Filename          ---     Relative Path of the Script
//                    a_ActualScriptType  ---     Type Of the Script
// Returns:           <none>
// Steps	:
//  1. Get the Object from the MainMap of the DataBase with a_DeviceID.
//  2. Traverse the 'a_ActualScriptType' Map for the Entry 'a_FileName'
//  3. If found, Remove the <Key, Value> pair from that Map.
//  4. Check if the a_FileName exists in the m_ScriptsMap.
//      if Exists
//      {
//        Remove the entry form m_ScriptsMap.(The Object already deleted in Step 3)
//      }
//      else
//      {
//        //Nothing ToDo
//      }
//
void OC_DataBase_c::RemoveEntry
( OC_String_t a_DeviceID,
  OC_String_t a_Filename,
  OC_Long_t a_ActualScriptType)
{
  OC_ScriptInfo_c*              a_Object;
  OC_ScriptInfoMap_t::iterator  a_Iter;

  a_Iter = m_DataBase.find( a_DeviceID  );
  if( a_Iter != m_DataBase.end() )
  {
      a_Object = a_Iter->second;
      switch( a_ActualScriptType  )
      {
        case OC_Scripts_DataAcq_e:
            RemoveReferences( a_DeviceID, a_Filename, a_ActualScriptType, a_Object->DataAcqScriptsMapReference());
            break;
        case OC_Scripts_Common_e:
            RemoveReferences( a_DeviceID, a_Filename, a_ActualScriptType, a_Object->CommonScriptsMapReference());
            break;
        case OC_Scripts_STicket_e:
            RemoveReferences( a_DeviceID, a_Filename, a_ActualScriptType, a_Object->STicketScriptsMapReference());
            break;
        case OC_Scripts_Decode_e:
            RemoveReferences( a_DeviceID, a_Filename, a_ActualScriptType, a_Object->DecodeScriptsMapReference());
            break;
        case OC_Scripts_Parse_e:
            RemoveReferences( a_DeviceID, a_Filename, a_ActualScriptType, a_Object->ParseScriptsMapReference());
            break;
        case OC_Scripts_FWUpdate_e:
            RemoveReferences( a_DeviceID, a_Filename, a_ActualScriptType, a_Object->FWUpdateScriptsMapReference());
            break;
        case OC_Scripts_Test_e:
            RemoveReferences( a_DeviceID, a_Filename, a_ActualScriptType, a_Object->TestScriptsMapReference());
            break;
      }// End Of Switch
  }
  else
  {
    OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg_P1(OC_MSGSET_SCRIPT_DATABASE,
                                                                      OC_MSG_SCRIPT_DATABASE_INVALID_SCRIPT_REFERENCE_ERROR,
                                                                      "ScriptName",
                                                                      a_Filename));
  }
}


//********************************************************************
// Class:             OC_DataBase_c
// Method:            RemoveReferences
// Description:       Removes an object from the DataBase.
// Parameters	:       a_DeviceID          ---     VendorID + ProductID
//                    a_Filename          ---     Relative Path of the Script
//                    a_ActualScriptType  ---     Type Of the Script
// Returns:           <none>
// Steps	:
//  1. Get the Object from the MainMap of the DataBase with a_DeviceID.
//  2. Traverse the 'a_ActualScriptType' Map for the Entry 'a_FileName'
//  3. If found, Remove the <Key, Value> pair from that Map.
//  4. Check if the a_FileName exists in the m_ScriptsMap.
//      if Exists
//      {
//        Remove the entry form m_ScriptsMap.(The Object already deleted in Step 3)
//      }
//      else
//      {
//        //Nothing ToDo
//      }
void OC_DataBase_c::RemoveReferences
( OC_String_t             a_DeviceID,
  OC_String_t             a_Filename,
  OC_ULong_t              a_ScriptType,
  OC_CommonScriptsMap_t&  a_MapRef)
{
  OC_StringList_t                     a_DeviceAssociationList;
  OC_CommonScriptsMap_t::iterator     a_CommonIter;
  OC_StringList_t::iterator           a_SIter;

  a_CommonIter = a_MapRef.find(a_Filename);
  if( a_CommonIter != a_MapRef.end() )
  {
    OC_Common_ScriptInfo_c* a_CommonObject;
    a_CommonObject = (OC_Common_ScriptInfo_c*)a_CommonIter->second;
    //Set Other Entries to NULL Before Proceeding.
    a_DeviceAssociationList = a_CommonObject->GetDeviceAssociationList();
    for(  a_SIter = a_DeviceAssociationList.begin();
          a_SIter != a_DeviceAssociationList.end();
          a_SIter++)
    {
        OC_ScriptInfoMap_t::iterator  a_IntermIter;
        OC_String_t                   a_ID = a_SIter->c_str();
        a_IntermIter = m_DataBase.find( a_ID );
        if( a_ID != a_DeviceID)
        {
          if( a_IntermIter != m_DataBase.end() )
          {
            OC_ScriptInfo_c*              a_IntermObject;
            a_IntermObject = a_IntermIter->second;

            switch( a_ScriptType  )
            {
              case OC_Scripts_DataAcq_e:
              {
                  OC_CommonScriptsMap_t& a_IntermMap  = a_IntermObject->DataAcqScriptsMapReference();
                  OC_CommonScriptsMap_t::iterator    a_IntermDataAcqIter;
                  a_IntermDataAcqIter = a_IntermMap.find(a_Filename);
                  if( a_IntermDataAcqIter != a_IntermMap.end() )
                  {
                    a_IntermDataAcqIter->second = NULL;
                    a_IntermMap.erase(a_Filename);
                  }
                  break;
              }
              case OC_Scripts_Common_e:
              {
                  OC_CommonScriptsMap_t& a_IntermMap  = a_IntermObject->CommonScriptsMapReference();
                  OC_CommonScriptsMap_t::iterator       a_IntermCommonIter;
                  a_IntermCommonIter = a_IntermMap.find(a_Filename);
                  if( a_IntermCommonIter != a_IntermMap.end() )
                  {
                    a_IntermCommonIter->second = NULL;
                    a_IntermMap.erase(a_Filename);
                  }
                  break;
              }
              case OC_Scripts_STicket_e:
              {
                  OC_STicketScriptsMap_t& a_IntermMap  = a_IntermObject->STicketScriptsMapReference();
                  OC_STicketScriptsMap_t::iterator       a_IntermSTicketIter;
                  a_IntermSTicketIter = a_IntermMap.find(a_Filename);
                  if( a_IntermSTicketIter != a_IntermMap.end() )
                  {
                    a_IntermSTicketIter->second = NULL;
                    a_IntermMap.erase(a_Filename);
                  }
                  break;
              }
              case OC_Scripts_Decode_e:
              {
                  OC_DecodeScriptsMap_t& a_IntermMap  = a_IntermObject->DecodeScriptsMapReference();
                  OC_DecodeScriptsMap_t::iterator       a_IntermDecodeIter;
                  a_IntermDecodeIter = a_IntermMap.find(a_Filename);
                  if( a_IntermDecodeIter != a_IntermMap.end() )
                  {
                    a_IntermDecodeIter->second = NULL;
                    a_IntermMap.erase(a_Filename);
                  }
                  break;
              }
              case OC_Scripts_Parse_e:
              {
                  OC_ParseScriptsMap_t& a_IntermMap  = a_IntermObject->ParseScriptsMapReference();
                  OC_ParseScriptsMap_t::iterator       a_IntermParseIter;
                  a_IntermParseIter = a_IntermMap.find(a_Filename);
                  if( a_IntermParseIter != a_IntermMap.end() )
                  {
                    a_IntermParseIter->second = NULL;
                    a_IntermMap.erase(a_Filename);
                  }
                  break;
              }
              case OC_Scripts_FWUpdate_e:
              {
                  OC_FWUpdateScriptsMap_t& a_IntermMap  = a_IntermObject->FWUpdateScriptsMapReference();
                  OC_FWUpdateScriptsMap_t::iterator       a_IntermFWUpdateIter;
                  a_IntermFWUpdateIter = a_IntermMap.find(a_Filename);
                  if( a_IntermFWUpdateIter != a_IntermMap.end() )
                  {
                    a_IntermFWUpdateIter->second = NULL;
                    a_IntermMap.erase(a_Filename);
                  }
                  break;
              }
              case OC_Scripts_Test_e:
              {
                  OC_TestScriptsMap_t& a_IntermMap  = a_IntermObject->TestScriptsMapReference();
                  OC_TestScriptsMap_t::iterator       a_IntermTestIter;
                  a_IntermTestIter = a_IntermMap.find(a_Filename);
                  if( a_IntermTestIter != a_IntermMap.end() )
                  {
                    a_IntermTestIter->second = NULL;
                    a_IntermMap.erase(a_Filename);
                  }
                  break;
              }
            }// Swith
          }// Found in the DataBase // IF
        }// DeviceIDs Not Equal
    }//For Loop
    //Delete the ActualObject;
    delete a_CommonIter->second;
    a_MapRef.erase(a_Filename);
  }
}

//********************************************************************
//
// Class	:               OC_ScriptInfo_c
// Method	:               IsScriptExist
// Description	:         Returns true if Script exists in the databse false otherwise;
// Parameters	:           a_ScriptName
// Returns	:             boolean value
bool OC_ScriptInfo_c::IsScriptExist
(OC_String_t a_ScriptName)
{
  OC_Common_ScriptInfo_c *    a_ReturnObject=NULL;
  a_ReturnObject=GetObject(a_ScriptName);
  if(strcmp(a_ScriptName.c_str(), a_ReturnObject->GetScriptName().c_str()) == 0)
    return(true);
  else
    return(false);
}


bool  OC_DataBase_c::IsScriptExist
(OC_String_t    a_ScrName,
 OC_String_t    a_DeviceID,
 OC_Scripts_t   a_ScrType)
{

  OC_ScriptInfoMap_t::iterator      a_Iter;
  OC_String_t                       a_ScriptName  =  a_ScrName;
  OC_ScriptInfo_c*                  a_pScrInfo  = NULL;
  bool                              a_Status  = true; //Script Exist..

  // The script name may be a relative path name or just a script name..
  a_Iter  = m_DataBase.find(a_DeviceID);
  if(a_Iter != m_DataBase.end())
  {
    a_pScrInfo = a_Iter->second;
  }
  else
  {
    OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg_P1(OC_MSGSET_SCRIPT_DATABASE,OC_MSG_SCRIPT_DATABASE_NOENTRY_ERROR, "DeviceID", a_DeviceID),
                    0,0,NULL,OC_Event_c::OC_DetailLevel_2_e,8,NULL,NULL);
    a_Status  = false;
    return(a_Status);
  }
  if(a_pScrInfo)
  {
    OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg_P1(OC_MSGSET_SCRIPT_DATABASE,OC_MSG_SCRIPT_DATABASE_NOENTRY_ERROR, "DeviceID", a_DeviceID),
                   0,0,NULL,OC_Event_c::OC_DetailLevel_2_e,8,NULL,NULL);
    a_Status  = false;
    return(a_Status);
  }
  // we have an entry for device ID...
  if(a_ScrName.find_last_of(OC_PlatformFactory_c::m_pCurrent->FName_GetSeparator()) == string::npos)
  {
    //Construct relative path name based on Script type...
    switch(a_ScrType)
    {
      case OC_Scripts_Common_e  :
        a_ScriptName  = OC_IMMSTRING("common") + OC_PlatformFactory_c::m_pCurrent->FName_GetSeparator() + a_ScrName;
        break;
      case OC_Scripts_DataAcq_e  :
        a_ScriptName  = OC_IMMSTRING("dataacq") + OC_PlatformFactory_c::m_pCurrent->FName_GetSeparator() + a_ScrName;
        break;
      case OC_Scripts_Decode_e  :
        a_ScriptName  = OC_IMMSTRING("decode") + OC_PlatformFactory_c::m_pCurrent->FName_GetSeparator() + a_ScrName;
        break;
      case OC_Scripts_Parse_e  :
        a_ScriptName  = OC_IMMSTRING("parse") + OC_PlatformFactory_c::m_pCurrent->FName_GetSeparator() + a_ScrName;
        break;
      case OC_Scripts_STicket_e  :
        a_ScriptName  = OC_IMMSTRING("sticket") + OC_PlatformFactory_c::m_pCurrent->FName_GetSeparator() + a_ScrName;
        break;
      case OC_Scripts_FWUpdate_e  :
        a_ScriptName  = OC_IMMSTRING("fwupdate") + OC_PlatformFactory_c::m_pCurrent->FName_GetSeparator() + a_ScrName;
        break;
      case OC_Scripts_Test_e  :
        a_ScriptName  = OC_IMMSTRING("test") + OC_PlatformFactory_c::m_pCurrent->FName_GetSeparator() + a_ScrName;
        break;
      default :
        OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg(OC_MSGSET_SCRIPT_DATABASE,OC_MSG_SCRIPT_DATABASE_INVALID_SCRIPT_TYPE),
                   0,0,NULL,OC_Event_c::OC_DetailLevel_2_e,8,NULL,NULL);
        a_Status  = false;
        return(a_Status);
    }
  }
  a_Status  = a_pScrInfo->IsScriptExist(a_ScriptName);
  return(a_Status);
}

OC_StringList_t OC_DataBase_c::Get_ScriptList
(OC_String_t    a_DeviceID,
 OC_Scripts_t   a_ScrType)
{
  OC_ScriptInfoMap_t::iterator      a_Iter;
  OC_ScriptInfo_c*                  a_pScrInfo  = NULL;

  a_Iter  = m_DataBase.find(a_DeviceID);
  if(a_Iter != m_DataBase.end())
  {
    a_pScrInfo = a_Iter->second;
  }
  else
  {
    OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg_P1(OC_MSGSET_SCRIPT_DATABASE,OC_MSG_SCRIPT_DATABASE_NOENTRY_ERROR, "DeviceID", a_DeviceID),
                    0,0,NULL,OC_Event_c::OC_DetailLevel_2_e,8,NULL,NULL);
    return(OC_StringList_t());
  }
  if(a_pScrInfo)
  {
    OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg_P1(OC_MSGSET_SCRIPT_DATABASE,OC_MSG_SCRIPT_DATABASE_NOENTRY_ERROR, "DeviceID", a_DeviceID),
                    0,0,NULL,OC_Event_c::OC_DetailLevel_2_e,8,NULL,NULL);
    return(OC_StringList_t());
  }
  return(a_pScrInfo->GetScrList(a_ScrType));
}

OC_StringList_t OC_ScriptInfo_c::GetScrList
(OC_Scripts_t     a_ScrType)
{

  OC_StringList_t       a_ScrList;

  if(a_ScrType  == OC_Scripts_Common_e )
  {
    OC_CommonScriptsMap_t::iterator   a_Iter;
    for(a_Iter  = m_CommonScriptsMap.begin(); a_Iter != m_CommonScriptsMap.end(); a_Iter++)
    {
      a_ScrList.push_back(a_Iter->first);
    }
  }
  else if(a_ScrType  ==  OC_Scripts_DataAcq_e)
  {
      OC_DataAcqScriptsMap_t::iterator   a_Iter;
      for(a_Iter  = m_DataAcquisitionScriptsMap.begin(); a_Iter != m_DataAcquisitionScriptsMap.end(); a_Iter++)
      {
         a_ScrList.push_back(a_Iter->first);
      }
  }
  else if(a_ScrType  ==  OC_Scripts_Decode_e )
  {
      OC_DecodeScriptsMap_t::iterator   a_Iter;
      for(a_Iter  = m_DecodeScriptsMap.begin(); a_Iter != m_DecodeScriptsMap.end(); a_Iter++)
      {
         a_ScrList.push_back(a_Iter->first);
      }
  }
  else if(a_ScrType  ==  OC_Scripts_Parse_e)
  {
      OC_ParseScriptsMap_t::iterator   a_Iter;
      for(a_Iter  = m_ParseScriptsMap.begin(); a_Iter != m_ParseScriptsMap.end(); a_Iter++)
      {
         a_ScrList.push_back(a_Iter->first);
      }
  }
  else if(a_ScrType  ==  OC_Scripts_STicket_e)
  {
      OC_STicketScriptsMap_t::iterator   a_Iter;
      for(a_Iter  = m_STicketScriptsMap.begin(); a_Iter != m_STicketScriptsMap.end(); a_Iter++)
      {
         a_ScrList.push_back(a_Iter->first);
      }
  }
  else if(a_ScrType  ==  OC_Scripts_FWUpdate_e)
  {
      OC_FWUpdateScriptsMap_t::iterator   a_Iter;
      for(a_Iter  = m_FWUpdateScriptsMap.begin(); a_Iter != m_FWUpdateScriptsMap.end(); a_Iter++)
      {
         a_ScrList.push_back(a_Iter->first);
      }
  }
  else if(a_ScrType  ==  OC_Scripts_Test_e)
  {
      OC_TestScriptsMap_t::iterator   a_Iter;
      for(a_Iter  = m_TestScriptsMap.begin(); a_Iter != m_TestScriptsMap.end(); a_Iter++)
      {
         a_ScrList.push_back(a_Iter->first);
      }
  }
  else
  {
    OC_PublishEvent(OC_Event_c::OC_Type_ErrorMsg_e,OC_LocalizedMsg(OC_MSGSET_SCRIPT_DATABASE,OC_MSG_SCRIPT_DATABASE_INVALID_SCRIPT_TYPE),
                   0,0,NULL,OC_Event_c::OC_DetailLevel_2_e,8,NULL,NULL);
  }
  return(a_ScrList);
}
