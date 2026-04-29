%{
#include <stdlib.h>
#include <string.h>
#include "y.tab.h"
void yyerror(char *);

// Helper to log tokens to a file for the Streamlit GUI Visualizer
void log_token(const char* token_type, const char* lexeme) {
    FILE *fp = fopen("tokens.txt", "a");
    if (fp) {
        fprintf(fp, "[%-15s] : %s\n", token_type, lexeme);
        fclose(fp);
    }
}
%}

%%

"#".* { /* SINGLE LINE COMMENT - IGNORED */ }

"int"           { log_token("TYPE", yytext); return TYPE_INT; }
"float"         { log_token("TYPE", yytext); return TYPE_FLOAT; }
"void"          { log_token("TYPE", yytext); return TYPE_VOID; }

"+"             { log_token("OPERATOR", yytext); return PLUS; }
"-"             { log_token("OPERATOR", yytext); return MINUS; }
"/"             { log_token("OPERATOR", yytext); return DIV; }
"*"             { log_token("OPERATOR", yytext); return MULT; }
">"             { log_token("OPERATOR", yytext); return GT; }
"<"             { log_token("OPERATOR", yytext); return LT; }
">="            { log_token("OPERATOR", yytext); return GE; }
"<="            { log_token("OPERATOR", yytext); return LE; }
"=="            { log_token("OPERATOR", yytext); return EQ; }
"!="            { log_token("OPERATOR", yytext); return NE; }
"&&"            { log_token("LOGICAL", yytext); return AND; }
"||"            { log_token("LOGICAL", yytext); return OR; }
"="             { log_token("ASSIGN", yytext); return ASSIG; }

"const"         { log_token("KEYWORD", yytext); return CONST; }
"for"           { log_token("KEYWORD", yytext); return FOR; }
"while"         { log_token("KEYWORD", yytext); return WHILE; }
"if"            { log_token("KEYWORD", yytext); return IF; }
"else"          { log_token("KEYWORD", yytext); return ELSE; }
"switch"        { log_token("KEYWORD", yytext); return SWITCH; }
"case"          { log_token("KEYWORD", yytext); return CASE; }
"repeat"        { log_token("KEYWORD", yytext); return REPEAT; }
"until"         { log_token("KEYWORD", yytext); return UNTIL; }
"break"         { log_token("KEYWORD", yytext); return BREAK; }
"continue"      { log_token("KEYWORD", yytext); return CONTINUE; }
"print"         { log_token("KEYWORD", yytext); return PRINT; }
"def"           { log_token("KEYWORD", yytext); return METHOD_DEF; }

"false"         {
                    log_token("BOOLEAN", yytext);
                    yylval.bValue = false;
                    return BOOL;
                }
"true"          {
                    log_token("BOOLEAN", yytext);
                    yylval.bValue = true;
                    return BOOL;
                }

[a-zA-Z][a-zA-Z0-9]* {
                        log_token("IDENTIFIER", yytext);
                        strcpy(yylval.sValue, yytext);
                        return VARIABLE;
                      }

[0-9]+[a-zA-Z]+[a-zA-Z0-9]* {
                        log_token("ERROR", "Wrong Variable Name");
                        return WRONG_VARIABLE;
                    }

@[a-zA-Z][a-zA-Z0-9]* {
                        log_token("METHOD_VAR", yytext);
                        strcpy(yylval.sValue, yytext);
                        return METHOD_VARIABLE;
                    }

[$][a-zA-Z][a-zA-Z0-9]* {
                        log_token("METHOD_NAME", yytext);
                        strcpy(yylval.sValue, yytext);
                        return METHOD;
                    }

[0-9]+              {
                        log_token("INTEGER", yytext);
                        yylval.iValue = atoi(yytext);
                        return INTEGER;
                    }

[0-9]+[.][0-9]+     {
                        log_token("FLOAT", yytext);
                        yylval.fValue = atof(yytext);
                        return FLOAT;
                    }

[\"][^"]*[\"]       {
                        log_token("STRING", yytext);
                        strcpy(yylval.sValue, yytext);
                        return STRING;
                    }

[()/;:{}.,]         {
                        log_token("PUNCTUATION", yytext);
                        return *yytext;
                    }

[ \t\n]+            ;       /* ignore whitespace */

.                   {
                        yyerror("Unknown character");
                    }
%%

int yywrap(void) {
    return 1;
}
