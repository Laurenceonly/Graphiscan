import React from 'react'
import { Text, View } from 'react-native'
import { Body, styles, useColors } from './ui'

// Render the supplied text verbatim, adding hierarchy to numbered section titles.
export default function AgreementContent({ content }: { content: string }) {
  const colors = useColors()
  return <View style={{ gap: 16 }}>{content.split(/\r?\n\s*\r?\n/).map((paragraph, index) =>
    /^\d+\.\s+[^\r\n]+$/.test(paragraph.trim())
      ? <Text key={index} accessibilityRole="header" style={[styles.body, { color: colors.text, fontWeight: '700', marginTop: index ? 8 : 0 }]}>{paragraph}</Text>
      : <Body key={index}>{paragraph}</Body>
  )}</View>
}
