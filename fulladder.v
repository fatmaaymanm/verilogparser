module fulladder (X, Y, Ci, Co, S);
input(X, Y, Ci);
output(Co, S);

assign S = X ^ Y ^ Ci;
assign Co = (X & Y) | (Y & Ci) |(X & Ci);
endmodule
