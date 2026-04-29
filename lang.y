%code requires {
    #include "lang.h"

    nodeType *conInt(int value);
    nodeType *conFloat(float value);
    nodeType *conStr(char *value);
    nodeType *conBool(bool value);
    nodeType *id(char *s);
    nodeType *symbolTable[SYM_LIMIT];
    nodeType *methodsSymbolTable[SYM_LIMIT];
    nodeType *methodOperands[METHOD_OPERANDS_LIMIT];
    nodeType *opr(int oper, int nops, ...);
    nodeType *setAndDeclare(char *variableName, nodeType* rhs, bool isConst);
    nodeType *defineMethod(char *methodName, nodeType* statements);
    nodeType *callMethod(char *methodName);
    int isVariableDeclared(char *variableName);
    int isMethodDeclared(char *methodName);
    int ex(nodeType *p);
    void addOperand(char *variableName);
    void passOperand(nodeType *p);
    void yyerror(char *);
    void printSymTable(int choice);
    
    /* AST JSON Functions */
    void init_ast_json();
    void close_ast_json();
    void append_ast_json(nodeType *p);
    void print_json_node(nodeType *p, FILE *fp);
    char* getOpName(int oper);

    static bool boolFile;
}
%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <stdbool.h>
#include <math.h>
#define YYERROR_VERBOSE

int yylex(void);
int variablesCount = 0;
int methodsCount = 0;
int operandsCount = 0;
int astStmtCount = 0;

%}

%union {
    int iValue;                 /* integer value */
    char sValue[100];           /* string Value */
    bool bValue;                
    float fValue;
    nodeType *nPtr;             /* node pointer */
};

%token<iValue> INTEGER 
%token<iValue> typeMissMatch 
%token<fValue>FLOAT 
%token<sValue>STRING 
%token<bValue>BOOL 
%token<sValue>VARIABLE 
%token<sValue>METHOD METHOD_VARIABLE

/* NEW C-STYLE TYPE TOKENS */
%token TYPE_INT TYPE_FLOAT TYPE_VOID

%token WHILE IF PRINT CONST METHOD_DEF FOR SWITCH CASE REPEAT UNTIL BREAK CONTINUE GE LE EQ NE GT LT AND OR MINUS PLUS MULT DIV ASSIG WRONG_VARIABLE
%nonassoc IFX
%nonassoc ELSE

%left GE LE EQ NE GT LT AND OR
%left PLUS MINUS
%left MULT DIV
%left ','
%nonassoc ASSIG
%nonassoc UMINUS
%nonassoc ':'
%nonassoc ';'
%nonassoc '('
%nonassoc '{'

%type<nPtr> val expr assignStmt logicExpr stmt stmtList caseStmt
%%

program:
        function                {boolFile=false; close_ast_json(); exit(0);}  
        ;

function:
          function stmt         {append_ast_json($2); ex($2);}
        |
        ;

stmt:
          ';'                                                           {$$ = opr(';', 2, NULL, NULL);}
        | PRINT expr ';'                                                {$$ = opr(PRINT, 1, $2);}                                         
        | BREAK ';'                                                     {$$ = opr(BREAK, 0);} 
        | CONTINUE ';'                                                  {$$ = opr(CONTINUE, 0);} 
        | SWITCH '(' val ')' '{' caseStmt '}'                           {$$ = opr(SWITCH, 2, $3, $6);} 
        | assignStmt ';'                                                {$$ = $1;}
        | REPEAT '{' stmtList '}' UNTIL '(' logicExpr ')' ';'           {$$ = opr(REPEAT, 2, $3, $7);}
        | WHILE '(' logicExpr ')' '{' stmtList '}'                      {$$ = opr(WHILE, 2, $3, $6);} 
        | METHOD '(' passedOperand ')' ';'                              {$$ = callMethod($1);}
        | METHOD_DEF METHOD '(' methodOperand ')' '{' stmtList '}'      {$$ = defineMethod($2, $7);}
        | FOR '(' assignStmt ';' logicExpr ';' assignStmt ')' '{' stmtList '}'  {$$ = opr(FOR, 4, $3, $5, $7, $10);}
        | IF '(' logicExpr ')' '{' stmtList '}' %prec IFX               {$$ = opr(IF, 2, $3, $6);}                
        | IF '(' logicExpr ')' '{' stmtList '}' ELSE '{' stmtList '}'   {$$ = opr(IF, 3, $3, $6, $10);}
        | '{' stmtList '}'                                              {$$ = $2;}
        | wrongAssigStmt                                                {}
        ;

wrongAssigStmt:        
          WRONG_VARIABLE ASSIG expr                                     {yyerror("wrong variable name");}
        | CONST WRONG_VARIABLE ASSIG expr                               {yyerror("wrong variable name");}
        ;

/* UPDATED TO ACCEPT C-STYLE DECLARATIONS */
assignStmt:
          VARIABLE ASSIG expr                                           {$$ = setAndDeclare($1, $3, false);}
        | TYPE_INT VARIABLE ASSIG expr                                  {$$ = setAndDeclare($2, $4, false);}
        | TYPE_FLOAT VARIABLE ASSIG expr                                {$$ = setAndDeclare($2, $4, false);}
        | TYPE_VOID VARIABLE ASSIG expr                                 {$$ = setAndDeclare($2, $4, false);}
        | METHOD_VARIABLE ASSIG expr                                    {$$ = setAndDeclare($1, $3, false);}
        | CONST VARIABLE ASSIG expr                                     {$$ = setAndDeclare($2, $4, true);}
        | CONST TYPE_INT VARIABLE ASSIG expr                            {$$ = setAndDeclare($3, $5, true);}
        | CONST TYPE_FLOAT VARIABLE ASSIG expr                          {$$ = setAndDeclare($3, $5, true);}
        ;

caseStmt:
           CASE val ':' stmtList BREAK ';'                              {$$ = opr(CASE, 2, $2, $4); }
        |  CASE val ':' stmtList BREAK ';' caseStmt                     {$$ = opr(CASE, 3, $2, $4, $7);}
        ;

stmtList:
          stmt                  {$$ = $1;} 
        | stmtList stmt         {$$ = opr(';', 2, $1, $2);} 
        ;

expr:
          MINUS expr %prec UMINUS       {$$ = opr(UMINUS, 1, $2);}
        | val                           {$$ = $1;}           
        | expr MULT expr                {$$ = opr(MULT, 2, $1, $3);}
        | expr DIV expr                 {$$ = opr(DIV, 2, $1, $3);}
        | expr PLUS expr                {$$ = opr(PLUS, 2, $1, $3);}
        | expr MINUS expr               {$$ = opr(MINUS, 2, $1, $3);}
        | '(' expr ')'                  {$$ = $2;}
        ;

logicExpr: 
          logicExpr GT logicExpr           {$$ = opr(GT, 2, $1, $3);} 
        | logicExpr LT logicExpr           {$$ = opr(LT, 2, $1, $3);} 
        | logicExpr GE logicExpr           {$$ = opr(GE, 2, $1, $3);} 
        | logicExpr NE logicExpr           {$$ = opr(NE, 2, $1, $3);} 
        | logicExpr LE logicExpr           {$$ = opr(LE, 2, $1, $3);} 
        | logicExpr EQ logicExpr           {$$ = opr(EQ, 2, $1, $3);} 
        | logicExpr AND logicExpr          {$$ = opr(AND, 2, $1, $3);} 
        | logicExpr OR logicExpr           {$$ = opr(OR, 2, $1, $3);} 
        | val                              {$$ = $1;} 
        ;

val:
          BOOL         {$$ = conBool($1);}    
        | STRING       {$$ = conStr($1);}     
        | INTEGER      {$$ = conInt($1);}     
        | FLOAT        {$$ = conFloat($1);}     
        | VARIABLE     {$$ = id($1);}
        | METHOD_VARIABLE     {$$ = id($1);}
        ;

passedOperand:
          val                                          {passOperand($1);} 
        | passedOperand ',' passedOperand            
        | ; 

methodOperand:
          METHOD_VARIABLE                              {addOperand($1);}
        | methodOperand ',' methodOperand            
        | ; 

%%

int getDataType(nodeType *node) {
    int dataType;
    if (node->type == typeCon) dataType = node->con.dataType;
    else if (node->type == typeId) dataType = node->id.dataType;
    else if (node->type == typeOpr) dataType = node->opr.dataType;
    return dataType;
}

int isVariableDeclared(char *variableName) {
     for(int i = 0 ; i < variablesCount; i++) {
        if(strcmp(symbolTable[i]->id.variableName, variableName) == 0) return i;
    }
    return -1;
}

int isMethodDeclared(char *methodName) {
     for(int i = 0 ; i < methodsCount; i++) {
        if(strcmp(methodsSymbolTable[i]->mth.methodName, methodName) == 0) return i;
    }
    return -1;
}

void addOperand(char *variableName){
    nodeType *p;
    if ((p = malloc(sizeof(nodeType))) == NULL) yyerror("out of memory");
    p->type = typeId;
    strcpy(p->id.variableName, variableName);

    if(operandsCount >= METHOD_OPERANDS_LIMIT){ yyerror("Number of operands exceeded the limit"); return; }
    methodOperands[operandsCount] = p;
    operandsCount++;
}

void passOperand(nodeType *p){
    if(operandsCount >= METHOD_OPERANDS_LIMIT){ yyerror("Number of operands exceeded the limit"); return; }
    methodOperands[operandsCount] = p;
    operandsCount++;
}

nodeType *defineMethod( char *methodName, nodeType* statements){
    int methodIndex = isMethodDeclared(methodName);
    nodeType *p;
    int i;

    if ((p = malloc(sizeof(nodeType) + (operandsCount) * sizeof(nodeType *))) == NULL) yyerror("out of memory");
    if (methodIndex == -1) {
        if(methodsCount >= SYM_LIMIT) yyerror("Stack Overflow");
        methodIndex = methodsCount;
        if ((methodsSymbolTable[methodIndex] = malloc(sizeof(nodeType))) == NULL) yyerror("out of memory");
        
        methodsSymbolTable[methodIndex]->type = typeMth;
        methodsSymbolTable[methodIndex]->mth.nops = operandsCount;
        strcpy(methodsSymbolTable[methodIndex]->mth.methodName, methodName);
        printSymTable(1);
        
        p->type = typeMth;
        p->mth.type = typeD; 
        p->mth.nops = operandsCount;
        strcpy(p->mth.methodName, methodName);

        for (i = 0; i < operandsCount; i++) {
            p->mth.op[i] = methodOperands[i];
        }
        p->mth.op[operandsCount] = statements;
        methodsCount++;
    }
    else { yyerror("Method already defined"); }
    operandsCount = 0;
    return p;
}

nodeType *callMethod(char *methodName){
    int methodIndex = isMethodDeclared(methodName);
    if(methodIndex == -1) yyerror("Method undefined");
    else if (methodsSymbolTable[methodIndex]->mth.nops != operandsCount) yyerror("Number of operands do not match with defined method");

    nodeType *p;
    if ((p = malloc(sizeof(nodeType) + (operandsCount-1) * sizeof(nodeType *))) == NULL) yyerror("out of memory");
    
    p->type = typeMth;
    p->mth.type = typeC; 
    p->mth.nops = operandsCount;
    strcpy(p->mth.methodName, methodName);
    
    for (int i = 0; i < operandsCount; i++) {
        p->mth.op[i] = methodOperands[i];
    }
    operandsCount = 0;
    return p;
}

nodeType *setAndDeclare(char *variableName, nodeType* rhs, bool isConst) {
    int variableIndex = isVariableDeclared(variableName);
    int dataType = getDataType(rhs);
    if (variableIndex == -1) {
        if(variablesCount >= SYM_LIMIT) yyerror("Stack Overflow");
        variableIndex = variablesCount;
        if ((symbolTable[variableIndex] = malloc(sizeof(nodeType))) == NULL) yyerror("out of memory");
        
        symbolTable[variableIndex]->type = typeId;
        symbolTable[variableIndex]->id.dataType = dataType;
        symbolTable[variableIndex]->id.isConst = isConst;
        strcpy(symbolTable[variableIndex]->id.variableName, variableName);
        printSymTable(0);
        variablesCount++;
    }
    else {
        if(symbolTable[variableIndex]->id.isConst) yyerror("Can not change a constant value");
        else if(symbolTable[variableIndex]->id.dataType != dataType) yyerror("Type Mismatch");
    }
    return opr(ASSIG, 2, symbolTable[variableIndex], rhs);
}


nodeType *opr(int oper, int nops, ...) {
    va_list ap;
    nodeType *p;
    int i;
    if ((p = malloc(sizeof(nodeType) + (nops-1) * sizeof(nodeType *))) == NULL) yyerror("out of memory");
    
    p->type = typeOpr;
    p->opr.oper = oper;
    p->opr.nops = nops;

    va_start(ap, nops);
    for (i = 0; i < nops; i++) {
        p->opr.op[i] = va_arg(ap, nodeType*);
    }
    va_end(ap);
    
    if(oper == MULT || oper == PLUS || oper == DIV || oper == MINUS || oper == UMINUS) {
        int dataType = getDataType(p->opr.op[0]);
        for(int i=1; i<nops; i++) {
            if(!(p->opr.op[i]->type == typeId && p->opr.op[i]->id.variableName[0] == '@')) {
                if(dataType != getDataType(p->opr.op[i])) {
                    yyerror("Type Mismatch");
                    p->opr.dataType = typeMissMatch;
                }
            }
        }
        if(p->opr.dataType != typeMissMatch) p->opr.dataType = dataType;
        return p;
    }
    else if(oper == GT || oper == LT || oper == GE || oper == NE || oper == LE || oper == EQ || oper == AND || oper == OR){
        int dataType = getDataType(p->opr.op[0]);
        for(int i=1; i<nops; i++) {
            if(dataType != getDataType(p->opr.op[i])) {
                yyerror("Type Missmatch");
                p->opr.dataType = typeMissMatch;
            }
        }
        if(p->opr.dataType != typeMissMatch) p->opr.dataType = dataType;
    }
    return p;
}

nodeType *id(char *s) {
    nodeType *p;
    if ((p = malloc(sizeof(nodeType))) == NULL) yyerror("out of memory");

    p->type = typeId;
    strcpy(p->id.variableName, s);
    
    int variableIndex = isVariableDeclared(s);
    if( variableIndex == -1) {
        if(s[0] != '@') yyerror("Using undeclared variable");
    }
    else {
        p->id.dataType = symbolTable[variableIndex]->id.dataType;
    }
    return p;
}

nodeType *conInt(int value){
    nodeType *p;
    if ((p = malloc(sizeof(nodeType))) == NULL) yyerror("out of memory");
    p->type = typeCon;
    p->con.dataType = INTEGER;
    p->con.integerValue = value;
    return p;
}
nodeType *conFloat(float value){
    nodeType *p;
    if ((p = malloc(sizeof(nodeType))) == NULL) yyerror("out of memory");
    p->type = typeCon;
    p->con.dataType = FLOAT;
    p->con.floatValue = value;
    return p;
}
nodeType *conStr(char *value){
    nodeType *p;
    if ((p = malloc(sizeof(nodeType))) == NULL) yyerror("out of memory");
    p->type = typeCon;
    p->con.dataType = STRING;
    strcpy(p->con.stringValue, value);
    return p;
}
nodeType *conBool(bool value){
    nodeType *p;
    if ((p = malloc(sizeof(nodeType))) == NULL) yyerror("out of memory");
    p->type = typeCon;
    p->con.dataType = BOOL;
    p->con.boolValue = value;
    return p;
}

void yyerror(char *s) {
    FILE * fp = fopen ("errors.txt","a");
    fprintf(fp, "%s\n", s);
    fclose(fp);
}

void printSymTable(int choice) {
    FILE * fp = fopen ("SymbolTable.txt","a");
    if(choice == 0) {
        fprintf(fp, "Variable Name: %s, Is Constant: %s\n", symbolTable[variablesCount]->id.variableName, (symbolTable[variablesCount]->id.isConst)?"true":"false");
    }
    else {
        fprintf(fp, "Method Name: %s, Number of Operands: %d\n", methodsSymbolTable[methodsCount]->mth.methodName, methodsSymbolTable[methodsCount]->mth.nops);
    }
    fclose(fp);
}

char* getOpName(int oper) {
    switch(oper) {
        case WHILE: return "WHILE";
        case IF: return "IF";
        case PRINT: return "PRINT";
        case FOR: return "FOR";
        case SWITCH: return "SWITCH";
        case CASE: return "CASE";
        case REPEAT: return "REPEAT";
        case UNTIL: return "UNTIL";
        case BREAK: return "BREAK";
        case CONTINUE: return "CONTINUE";
        case GE: return ">=";
        case LE: return "<=";
        case EQ: return "==";
        case NE: return "!=";
        case GT: return ">";
        case LT: return "<";
        case AND: return "AND";
        case OR: return "OR";
        case MINUS: return "-";
        case UMINUS: return "- (unary)";
        case PLUS: return "+";
        case MULT: return "*";
        case DIV: return "/";
        case ASSIG: return "=";
        case ';': return "Statement Seq";
        default: return "Unknown Op";
    }
}

void print_json_node(nodeType *p, FILE *fp) {
    if (!p) { fprintf(fp, "null"); return; }
    fprintf(fp, "{");
    if (p->type == typeCon) {
        fprintf(fp, "\"type\": \"Constant\", ");
        if (p->con.dataType == INTEGER) fprintf(fp, "\"value\": \"%d\"", p->con.integerValue);
        else if (p->con.dataType == FLOAT) fprintf(fp, "\"value\": \"%f\"", p->con.floatValue);
        else if (p->con.dataType == STRING) fprintf(fp, "\"value\": \\\"%s\\\"", p->con.stringValue); 
        else if (p->con.dataType == BOOL) fprintf(fp, "\"value\": \"%s\"", p->con.boolValue ? "true" : "false");
    }
    else if (p->type == typeId) {
        fprintf(fp, "\"type\": \"Identifier\", \"value\": \"%s\"", p->id.variableName);
    }
    else if (p->type == typeOpr) {
        fprintf(fp, "\"type\": \"Operator\", \"value\": \"%s\"", getOpName(p->opr.oper));
        if (p->opr.nops > 0) {
            fprintf(fp, ", \"children\": [");
            for (int i = 0; i < p->opr.nops; i++) {
                print_json_node(p->opr.op[i], fp);
                if (i < p->opr.nops - 1) fprintf(fp, ", ");
            }
            fprintf(fp, "]");
        }
    }
    else if (p->type == typeMth) {
        fprintf(fp, "\"type\": \"Method\", \"value\": \"%s\"", p->mth.methodName);
        int max_ops = p->mth.type == typeD ? p->mth.nops + 1 : p->mth.nops;
        if (max_ops > 0) {
            fprintf(fp, ", \"children\": [");
            for(int i=0; i<max_ops; i++) {
                print_json_node(p->mth.op[i], fp);
                if (i < max_ops - 1) fprintf(fp, ", ");
            }
            fprintf(fp, "]");
        }
    }
    fprintf(fp, "}");
}

void init_ast_json() {
    FILE *fp = fopen("ast.json", "w");
    if (fp) {
        fprintf(fp, "{\"type\": \"Program\", \"children\": [\n");
        fclose(fp);
    }
}

void append_ast_json(nodeType *p) {
    if(!p) return;
    FILE *fp = fopen("ast.json", "a");
    if (fp) {
        if (astStmtCount > 0) fprintf(fp, ",\n");
        print_json_node(p, fp);
        astStmtCount++;
        fclose(fp);
    }
}

void close_ast_json() {
    FILE *fp = fopen("ast.json", "a");
    if (fp) {
        fprintf(fp, "\n]}\n");
        fclose(fp);
    }
}

int main(void) {
    init_ast_json();
    yyparse();
    return 0;
}
