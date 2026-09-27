package contract

import (
 "testing"
 rates "example.invalid/rates"
)

func TestContract(t *testing.T) {
 for _, c := range []struct{ units, want int }{{-1,0},{0,0},{1,125},{9,1125},{10,1000},{20,2000}} {
  if got := rates.Total(c.units); got != c.want { t.Fatalf("Total(%d)=%d; want %d", c.units, got, c.want) }
 }
}
