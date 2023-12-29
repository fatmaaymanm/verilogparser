module mux (input A, input B, input C, input D, input S, input R, output reg [2:0] O);

reg [3:0] L;
reg [3:0] N;
wire [2:0] M;
wire [2:0] U;

    always @(*)
        if (S && R)
            O = 1;
        else if (S || R)
            O = 2;
        else if (!S)
            O = 3;
        else if (!R)
            O = 4;
        else
            O = 0;

endmodule