import React from 'react'
import { View } from 'react-native'
import { Body, Button, styles } from './ui'

export default function QuickFilters({ label, value, options, onChange }: {
  label: string; value: string; options: { value: string; label: string }[]; onChange: (value: string) => void;
}) {
  return <View style={{ gap: 8 }}>
    <Body muted>{label}</Body>
    <View style={styles.wrap}>{options.map(option => <Button key={option.value} label={option.label} secondary={value !== option.value} selected={value === option.value} onPress={() => onChange(option.value)}/>)}</View>
  </View>
}
