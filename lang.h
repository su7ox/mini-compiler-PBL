#ifndef LANG_H
#define LANG_H

#include <stdbool.h>

#define SYM_LIMIT 100
#define METHOD_OPERANDS_LIMIT 10

typedef enum { typeCon, typeId, typeOpr, typeMth } nodeEnum;
typedef enum { typeD, typeC} nodeMethodType;

/* constants */
typedef struct {
    int dataType;
    union {
        int integerValue;
        float floatValue;
        char stringValue[100];
        bool boolValue;
    };
} conNodeType;

typedef struct {                     
    char variableName[100];
    int dataType;
    bool isConst;
} idNodeType;

/* operators */
typedef struct {
    int dataType;
    int oper;                  
    int nops;                  
    struct nodeTypeTag *op[1];	
} oprNodeType;

/* method operands */
typedef struct {
    nodeMethodType type;
    char methodName[100];       
    int nops;                   
    struct nodeTypeTag *op[1];	
} methodNodeType;

typedef struct nodeTypeTag {
    nodeEnum type;              

    union {
        conNodeType con;       
        idNodeType id;         
        oprNodeType opr;        
        methodNodeType mth;     
    };
} nodeType;

extern nodeType *symbolTable[SYM_LIMIT];
extern nodeType *methodsSymbolTable[SYM_LIMIT];

/* AST Node Structure */
typedef struct ASTNode {
    char* type;         
    char* value;         
    struct ASTNode* left;
    struct ASTNode* right;
} ASTNode;

ASTNode* createNode(char* type, char* value, ASTNode* left, ASTNode* right);
void write_ast_json(ASTNode* root, const char* filename);

#endif 
