module mux (input A, input B, input S, output reg O);

    always @(*)
        if (S) 
            O = A;
        else
            O = B;   
endmodule