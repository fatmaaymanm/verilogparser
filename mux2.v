module mux2 (input A, input B, input S, output O);

    assign O = S ? A : B;
    
endmodule