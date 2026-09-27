package rates

// Total returns the charge in cents, with the volume discount applied.
func Total(units int) int {
	if units < 0 { return 0 }
	price := 125
	if units >= 10 { price = 100 }
	return units * price
}
