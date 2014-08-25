//********************************************************************
//
// File         : oc_scriptdatabase.cpp
//
// Classes      : OC_DataBase_c
//                OC_ScriptInfo_c 
//                OC_Common_ScriptInfo_c
//                |-OC_DataAcquisition_ScriptInfo_c
//                |-OC_Test_ScriptInfo_c
//                |-OC_FWUpdate_ScriptInfo_c
//                |-OC_Decode_ScriptInfo_c
//                |-OC_Parse_ScriptInfo_c
//                |-OC_STicket_ScriptInfo_c
//
//                

#ifndef OC_ONCE_SCRIPTDATABASE
#define OC_ONCE_SCRIPTDATABASE

#include <oc_include.h>

const OC_ULong_t  g_MaxBufferLength         = 1024;

typedef enum 
{
  OC_Scripts_Common_e                       = 0,
  OC_Scripts_DataAcq_e                      = 1,
  OC_Scripts_Decode_e                       = 2,
  OC_Scripts_Parse_e                        = 3,
  OC_Scripts_STicket_e                      = 4,
  OC_Scripts_FWUpdate_e                     = 5,
  OC_Scripts_Test_e                         = 6
} OC_Scripts_t;

typedef enum
{
    OC_External_e = 0,
    OC_Internal_e
}OC_Option_type_t;

/*
Order of MetaData Attributes in a Script
1	TYPE:
2	VERSION:
3	RTEVERSION:
 	  [
4	    DEPENDENTSCRIPTS:
5	    DEVICEASSOC:
	    [
6	      TESTOPTION:
7	      TESTDESCRIPTION:
8	      TESTNAME:
      ]
	  ] 
9	[BKVERSION:]
*/


typedef enum 
{
  OC_ScriptAttribute_Type_e                 = 0,  //Should Be 0' as used in the ReadMetaData()
  OC_ScriptAttribute_Version_e              = 1,  //m_Attributes vector needs to be initialized in the same order!
  OC_ScriptAttribute_RTEVersion_e           = 2,
  OC_ScriptAttribute_BRKVersion_e           = 3,
  OC_ScriptAttribute_DependentScripts_e     = 4,
  OC_ScriptAttribute_SubScripts_e           = 5,
  OC_ScriptAttribute_DeviceAssoc_e          = 6,
  OC_ScriptAttribute_TestName_e             = 7, 
  OC_ScriptAttribute_TestDescription_e      = 8,
  OC_ScriptAttribute_TestIntOption_e        = 9,
  OC_ScriptAttribute_TestExtOption_e        = 10
}OC_ScriptAttributes_t;


//********************************************************************
//
// Class:       OC_Common_ScriptInfo_c
// Method: 
// Description: 
// Parameters:  <none>
// Returns:     <none>
// Comments:

class OC_Common_ScriptInfo_c
{
private:
  OC_String_t               m_ScriptName;
  OC_String_t               m_ScriptType;
	OC_String_t               m_ScriptVersion;
  OC_String_t               m_RteVersion;
  OC_String_t               m_BreakVersion;
protected:
  //Shared by all the Childs 
  OC_StringList_t           m_Attributes;  
  OC_StringList_t           m_DependentScripts;     //Immediate Dependency Information
  OC_StringList_t           m_SubScriptsList;       //List for Sub Scripts
  OC_ULong_t                m_CommonAttributeCount; //Holds the Count of the CommonAttributes;
  OC_String_t               m_ScriptsRootDirectory;

  void                      PopulateCommonMetaData    ( OC_Compression_c  a_Comp,
                                                        OC_String_t       a_FileName  );
  void                      PopulateCommonMetaData    ( OC_String_t       a_FileName );

  OC_String_t               GetAttributeValue         ( OC_String_t       a_Line,
                                                        OC_String_t       a_AttrName );     //This is just a helper Function to read the Value from Parameter One.
  void                      GetAttributeValueList     ( OC_String_t       a_ValueString,
                                                        OC_StringList_t&  a_ReturnList,
                                                        OC_Char_t         a_Delimetere  = ',',
                                                        bool              a_FlagDepList = false); //To fill the DepedencyList
//Ctor & Dtor
public:
                            OC_Common_ScriptInfo_c    ();
                            ~OC_Common_ScriptInfo_c   ();
  //Returns the Reference here;
  OC_StringList_t&          DependencyScriptsReference()  { return m_DependentScripts;  }
  OC_StringList_t&          SubScriptsReference       ()  { return m_SubScriptsList;    }
  // The following API is to get the Immediate Dependents, Called from Recursive Function
  OC_StringList_t           GetDependencyList         ()  { return m_DependentScripts;  }
  OC_StringList_t           GetSubScriptsList         ()  { return m_SubScriptsList;    }
  virtual OC_StringList_t   GetDeviceAssociationList  ()  { OC_StringList_t a_TempDevAssc;
							    OC_ASSERT_INVALIDPATH;
							    return(a_TempDevAssc);  } //Common Scripts are for all Devices;
  //Set Methods
  void                      SetScriptName             ( OC_String_t  a_ScriptName        )  { m_ScriptName    = a_ScriptName;    }
  void                      SetScriptType             ( OC_String_t  a_ScriptType        )  { m_ScriptType    = a_ScriptType;    }
  void                      SetScriptVersion          ( OC_String_t  a_ScriptVersion     )  { m_ScriptVersion = a_ScriptVersion; }
  void                      SetRTEVersion             ( OC_String_t  a_RteVersion        )  { m_RteVersion    = a_RteVersion;    }
  void                      SetBrokenVersion          ( OC_String_t  a_BrokenVersion     )  { m_BreakVersion   = a_BrokenVersion;}
  //Get Methods
  OC_String_t               GetScriptName             (void)  {return m_ScriptName;}
  OC_String_t               GetScriptType             (void)  {return m_ScriptType;}
  OC_String_t               GetScriptVersion          (void)  {return m_ScriptVersion;}
  OC_String_t               GetRTEVersion             (void)  {return m_RteVersion;}
  OC_String_t               GetBrokenVersion          (void)  {return m_BreakVersion;}

  // Reads MetaData Attributes from the fptr
  virtual void ReadMetaData         ( OC_String_t a_FileName, OC_Char_t a_Delimetere = ',');
};

//********************************************************************
//
// Class	:      OC_DataAcquisition_ScriptInfo_c
// Method	: 
// Description	: 
// Parameters	: <none>
// Returns	: <none>
// Comments	:
class OC_DataAcquisition_ScriptInfo_c: public OC_Common_ScriptInfo_c
{
private:
  OC_StringList_t           m_DeviceAssocList;
//Ctor & Dtor
public:
                            OC_DataAcquisition_ScriptInfo_c   (void); //Calls super to set the attributes.
                            ~OC_DataAcquisition_ScriptInfo_c  (void);
  void                      SetDeviceAssociation              (OC_StringList_t  a_DeviceAssociation)  
                                                              {m_DeviceAssocList = a_DeviceAssociation;}
  OC_StringList_t           GetDeviceAssociationList          (void)
                                                              {return m_DeviceAssocList;}
  // Reads metaData in the fileHandle and fills the attributes
  void                      ReadMetaData                      ( OC_String_t a_FileName,
                                                                OC_Char_t a_Delimetere = ',');
};

//********************************************************************
//
// Class	:      OC_Test_ScriptInfo_c
// Method	: 
// Description	: 
// Parameters	: <none>
// Returns	: <none>
// Comments	:

class OC_Test_ScriptInfo_c: public OC_Common_ScriptInfo_c
{


private:
  OC_String_t               m_TestName;
  OC_String_t               m_TestDescr;
  OC_String_t               m_GrpTestName;
  OC_String_t               m_GrpTestScrName;
  //OC_String_t             m_TestOption;
  OC_StringList_t           m_TestIntOption;
  OC_StringList_t           m_TestExtOption;
  OC_StringList_t           m_DeviceAssocList;
//Ctor & Dtor
public:
                            OC_Test_ScriptInfo_c      (void); //Calls parentCtor and populates 
                            ~OC_Test_ScriptInfo_c     (void);
  //Set Methods
  void                      SetTestName               (OC_String_t  a_TestName)   {m_TestName = a_TestName;}
  void                      SetTestDescription        (OC_String_t  a_TestDescr)  {m_TestDescr = a_TestDescr;}
  //void                      SetTestOption             (OC_String_t  a_TestOption) {m_TestOption = a_TestOption;}
  void                      SetTestOption             (OC_Option_type_t  Optiontype,
                                                       OC_String_t       Option);
  //Get Methods
  OC_String_t               GetTestName               (void){return m_TestName;}
  OC_String_t               GetTestDescription        (void){return m_TestDescr;}
  //OC_String_t               GetTestOption             (void){return m_TestOption;}
  OC_StringList_t           GetTestOption             (OC_Option_type_t  Optiontype);
  OC_StringList_t           GetDeviceAssociationList  (  void   )  {      return m_DeviceAssocList;   }

  void                      ReadMetaData              (OC_String_t a_FileName,
                                                       OC_Char_t a_Delimetere = ',');  
};

//********************************************************************
//
// Class	:      OC_FWUpdate_ScriptInfo_c
// Method	: 
// Description	: 
// Parameters	: <none>
// Returns	: <none>
// Comments	:

class OC_FWUpdate_ScriptInfo_c: public OC_Common_ScriptInfo_c 
{
private:
  OC_StringList_t           m_DeviceAssocList;
//Ctor & Dtor
public:
                            OC_FWUpdate_ScriptInfo_c    (void); //Calls super to set the attributes.
                            ~OC_FWUpdate_ScriptInfo_c   (void);
  //GetMethods
  OC_StringList_t           GetDeviceAssociationList    (void){return m_DeviceAssocList;}
  void                      ReadMetaData                (OC_String_t a_FileName,
                                                         OC_Char_t a_Delimetere = ',');  
};

//********************************************************************
//
// Class	:      OC_Decode_ScriptInfo_c
// Method	: 
// Description	: 
// Parameters	: <none>
// Returns	: <none>
// Comments	:

//Decode Scripts
class OC_Decode_ScriptInfo_c: public OC_Common_ScriptInfo_c 
{
private:
  OC_StringList_t           m_DeviceAssocList;
//Ctor & Dtor
public:
                            OC_Decode_ScriptInfo_c      (void); //Calls super to set the attributes.
                            ~OC_Decode_ScriptInfo_c     (void);
  //GetMethods
  OC_StringList_t           GetDeviceAssociationList    (void){return m_DeviceAssocList;}
  void                      ReadMetaData                ( OC_String_t a_FileName,
                                                          OC_Char_t a_Delimetere = ',');  
};

//********************************************************************
//
// Class	:      OC_Parse_ScriptInfo_c
// Method	: 
// Description	: 
// Parameters	: <none>
// Returns	: <none>
// Comments	:

class OC_Parse_ScriptInfo_c: public OC_Common_ScriptInfo_c 
{
private:
  OC_StringList_t           m_DeviceAssocList;
//Ctor & Dtor
public:
                            OC_Parse_ScriptInfo_c         (void); //Calls super to set the attributes.
                            ~OC_Parse_ScriptInfo_c        (void);
  OC_StringList_t           GetDeviceAssociationList      (void){return m_DeviceAssocList;}
  void                      ReadMetaData                  ( OC_String_t a_FileName,
                                                            OC_Char_t a_Delimetere = ',');  
};

//********************************************************************
//
// Class	:      OC_STicket_ScriptInfo_c
// Method	: 
// Description	: 
// Parameters	: <none>
// Returns	: <none>
// Comments	:

class OC_STicket_ScriptInfo_c: public OC_Common_ScriptInfo_c 
{
private:
  OC_StringList_t           m_DeviceAssocList;
//Ctor & Dtor
public:
                            OC_STicket_ScriptInfo_c   (void); //Calls super to set the attributes.
                            ~OC_STicket_ScriptInfo_c  (void);
  //GetMethods
  OC_StringList_t           GetDeviceAssociationList  (void){return m_DeviceAssocList;}
  void                      ReadMetaData              ( OC_String_t a_FileName,
                                                        OC_Char_t a_Delimetere = ',');  
};

typedef map< OC_String_t, OC_Common_ScriptInfo_c* >    OC_CommonScriptsMap_t;
typedef map< OC_String_t, OC_Common_ScriptInfo_c* >    OC_SubScriptsMap_t;
typedef map< OC_String_t, OC_Common_ScriptInfo_c* >    OC_STicketScriptsMap_t;
typedef map< OC_String_t, OC_Common_ScriptInfo_c* >    OC_FWUpdateScriptsMap_t;
typedef map< OC_String_t, OC_Common_ScriptInfo_c* >    OC_TestScriptsMap_t;
typedef map< OC_String_t, OC_Common_ScriptInfo_c* >    OC_DataAcqScriptsMap_t;
typedef map< OC_String_t, OC_Common_ScriptInfo_c* >    OC_DecodeScriptsMap_t;
typedef map< OC_String_t, OC_Common_ScriptInfo_c* >    OC_ParseScriptsMap_t;
typedef map< OC_String_t, OC_String_t>  OC_ScriptMap_t;

//********************************************************************
//
// Class	:      OC_ScriptInfo_c
// Method	: 
// Description	: 
// Parameters	: <none>
// Returns	: <none>
// Comments	:  Main ScriptInfo Class Declaration
class OC_ScriptInfo_c
{
private:
  static  OC_CommonScriptsMap_t             m_CommonScriptsMap; //Common Meta-Data For All the Scripts
  static  OC_SubScriptsMap_t                m_SubScriptsMap;    //SubScript Meta-Data For All the Scripts
          OC_STicketScriptsMap_t            m_STicketScriptsMap;
          OC_FWUpdateScriptsMap_t           m_FWUpdateScriptsMap;
          OC_TestScriptsMap_t               m_TestScriptsMap;
          OC_DataAcqScriptsMap_t            m_DataAcquisitionScriptsMap;
          OC_DecodeScriptsMap_t             m_DecodeScriptsMap;
          OC_ParseScriptsMap_t              m_ParseScriptsMap;
//Ctors and Dtors 
public:
                                            OC_ScriptInfo_c               (void);   //By default all the maps are of size 0
                                            ~OC_ScriptInfo_c              (void);
  //Methods for Member References
          OC_CommonScriptsMap_t&            CommonScriptsMapReference     (void){return m_CommonScriptsMap;}
          OC_SubScriptsMap_t&               SubScriptsMapReference        (void){return m_SubScriptsMap;}
          OC_STicketScriptsMap_t&           STicketScriptsMapReference    (void){return m_STicketScriptsMap;}
          OC_FWUpdateScriptsMap_t&          FWUpdateScriptsMapReference   (void){return m_FWUpdateScriptsMap;}
          OC_TestScriptsMap_t&              TestScriptsMapReference       (void){return m_TestScriptsMap;}
          OC_DataAcqScriptsMap_t&           DataAcqScriptsMapReference    (void){return m_DataAcquisitionScriptsMap;}
          OC_DecodeScriptsMap_t&            DecodeScriptsMapReference     (void){return m_DecodeScriptsMap;}
          OC_ParseScriptsMap_t&             ParseScriptsMapReference      (void){return m_ParseScriptsMap;}
          bool                              IsScriptExist                 (OC_String_t a_ScriptName);
          OC_ULong_t                        GetVersionAsNumber            ( OC_String_t a_VersionString);
          bool                              CheckDependency               ( OC_String_t a_ScriptName, 
                                                                            OC_StringList_t& a_DependencyList);
  //Getters Return the MetaData Object for the a_ScriptName
          OC_Common_ScriptInfo_c*           GetCommonObject               (OC_String_t a_ScriptName);
          OC_Common_ScriptInfo_c*           GetSubScriptObject            (OC_String_t a_ScriptName);
          OC_STicket_ScriptInfo_c*          GetSTicketObject              (OC_String_t a_ScriptName);
          OC_FWUpdate_ScriptInfo_c*         GetFWUpdateObject             (OC_String_t a_ScriptName);
          OC_Test_ScriptInfo_c*             GetTestObject                 (OC_String_t a_ScriptName);
          OC_DataAcquisition_ScriptInfo_c*  GetDataAcqObject              (OC_String_t a_ScriptName);
          OC_Decode_ScriptInfo_c*           GetDecodeObject               (OC_String_t a_ScriptName);
          OC_Parse_ScriptInfo_c*            GetParseObject                (OC_String_t a_ScriptName);
          OC_Common_ScriptInfo_c*           GetObject                     (OC_String_t a_ScriptName);
          OC_StringList_t                   GetScrList                    (OC_Scripts_t   a_ScrType);
};

typedef map< OC_String_t, OC_ScriptInfo_c* > OC_ScriptInfoMap_t;

//********************************************************************
//
// Class	:      OC_DataBase_c
// Method	: 
// Description	: 
// Parameters	: <none>
// Returns	: <none>
// Comments	:
class OC_DataBase_c
{
private:
    OC_ScriptInfoMap_t      m_DataBase;
    OC_ScriptMap_t          m_ScriptsMap;
    void                    DeallocateMaps();
    void                    RemoveReferences      ( OC_String_t             a_DeviceID,
                                                    OC_String_t             a_Filename,
                                                    OC_ULong_t              a_ScriptType,
                                                    OC_CommonScriptsMap_t&  a_MapRef      );
public:
  const OC_String_t g_lszCommonScriptsKey;
//Ctor, Dtor
public:
                            OC_DataBase_c         (void);
                            ~OC_DataBase_c        (void);
  //Helper function
  OC_Long_t                 GetScriptType         ( OC_String_t a_Path);
  //Populates the entire DataBase
  bool                      Initialize            (void);
  void                      UpdateMap             (OC_Common_ScriptInfo_c* a_MetaDataObject) ;
  void                      TraverseDirectories   ( OC_String_t a_RootDirectory,
                                                    OC_Long_t a_ActualScriptType  = -1  ) ; //-1 for Scripts Root Directory
  // Returns the Container Object for the Given Key.
  // Returns a MainObject pointer if the Key is found in DataBase NULL OtherWise
  OC_ScriptInfo_c*          GetScriptInfo         ( OC_String_t a_Key );
  void                      Refresh();
  void                      InsertEntry(OC_String_t a_Filename, OC_Long_t a_ActualScriptType);
  bool                      IsScriptExist(OC_String_t a_ScrName, OC_String_t a_DeviceID, OC_Scripts_t a_ScrType);
  OC_StringList_t           Get_ScriptList(OC_String_t a_DeviceID, OC_Scripts_t a_ScrType);
  void                      RemoveEntry           ( OC_String_t             a_DeviceID, 
                                                    OC_String_t             a_Filename, 
                                                    OC_Long_t               a_ActualScriptType  );
};


#endif //#ifndef OC_ONCE_SCRIPTDATABASE