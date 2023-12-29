module mux (input A, input B, input C, input D, input [1:0] S, output reg O);

reg [3:0] L;
wire [2:0] M;

    always @(*)
        case (S)
            2'b00: O = A;
            2'b01: O = B;
            2'b10: O = C;
            2'b11: O = D;
            default: O = 0;
        endcase
endmodule