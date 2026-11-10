import React from 'react'
import { ScrollView, View } from 'react-native'
import { Body, Button, styles } from './ui'

export default function QuickFilters({ label, value, options, onChange, hideLabel=false }: {
  label: string; value: string; options: { value: string; label: string }[]; onChange: (value: string) => void; hideLabel?:boolean;
}) {
  return <View style={{ gap: 8 }}>
    {!hideLabel&&<Body muted>{label}</Body>}
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ flexDirection: 'row', gap: 8 }}>
      {options.map(option => <Button key={option.value} label={option.label} secondary={value !== option.value} selected={value === option.value} onPress={() => onChange(option.value)} style={{ minHeight: 44, paddingHorizontal: 12 }}/>)}</ScrollView>
  </View>
}
