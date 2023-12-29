module fulladder (input X, input Y, input Ci, output Co, output S);

assign S = X ^ Y ^ Ci;
assign Co = (X & Y) | (Y & Ci) |(X & Ci);
endmodule
