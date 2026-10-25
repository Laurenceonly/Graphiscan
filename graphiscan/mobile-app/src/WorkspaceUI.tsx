import React from 'react'
import { Pressable, StyleSheet, Text, View } from 'react-native'
import MaterialIcons from '@expo/vector-icons/MaterialIcons'
import { dateLabel, screeningType } from './core/presentation'
import { Status, useColors } from './ui'
import BrandLogo from './BrandLogo'

type IconName = React.ComponentProps<typeof MaterialIcons>['name']

export function AppBrand() {
  const c = useColors()
  return <View style={s.brand} accessible accessibilityLabel="GraphiScan">
    <BrandLogo size={30}/>
    <Text style={[s.wordmark,{color:c.text}]}>Graphi<Text style={{color:c.brandAccent}}>Scan</Text></Text>
  </View>
}

export function Avatar({ name, size = 40 }: { name: string; size?: number }) {
  const c = useColors(), initials = name.trim().split(/\s+/).slice(0,2).map(part=>part[0]).join('').toUpperCase()
  return <View style={[s.avatar,{width:size,height:size,borderRadius:size/2,backgroundColor:c.soft}]}><Text style={{color:c.primary,fontSize:size*.36,fontWeight:'600'}}>{initials || 'G'}</Text></View>
}

export function SectionTitle({ title, action, onPress }: { title: string; action?: string; onPress?: () => void }) {
  const c = useColors()
  return <View style={s.sectionTitle}>
    <Text accessibilityRole="header" style={[s.sectionHeading,{color:c.text}]}>{title}</Text>
    {action&&onPress&&<Pressable accessibilityRole="button" onPress={onPress} style={s.textAction}><Text style={{color:c.primary,fontSize:13,fontWeight:'600'}}>{action}</Text></Pressable>}
  </View>
}

export function ActionRow({ title, detail, icon, onPress, last = false }: { title: string; detail: string; icon: IconName; onPress: () => void; last?: boolean }) {
  const c = useColors()
  return <Pressable accessibilityRole="button" accessibilityLabel={title} onPress={onPress} android_ripple={{color:c.soft}}
    style={({pressed})=>[s.actionRow,{borderBottomColor:c.border,borderBottomWidth:last?0:1,backgroundColor:pressed?c.soft:c.surface}]}>
    <MaterialIcons name={icon} size={24} color={c.primary} accessible={false}/>
    <View style={s.rowCopy}><Text style={[s.rowTitle,{color:c.text}]}>{title}</Text><Text style={[s.rowDetail,{color:c.muted}]}>{detail}</Text></View>
    <MaterialIcons name="chevron-right" size={22} color={c.muted} accessible={false}/>
  </Pressable>
}

export function ScreeningRow({ record, studentName, grade, onPress, last = false }: { record: any; studentName?: string; grade?:number; onPress: () => void; last?: boolean }) {
  const c = useColors(), name=studentName || 'Student '+record.student_id
  return <Pressable accessibilityRole="button" accessibilityLabel={'Open screening '+record.result_id} onPress={onPress} android_ripple={{color:c.soft}}
    style={({pressed})=>[s.screeningRow,{borderBottomColor:c.border,borderBottomWidth:last?0:1,backgroundColor:pressed?c.soft:c.surface}]}>
    <View style={s.recordTop}><Avatar name={name} size={36}/><View style={s.rowCopy}><Text style={[s.rowTitle,{color:c.text}]}>{name}</Text><Text style={[s.rowDetail,{color:c.muted}]}>{grade?'Grade '+grade+' · ':''}{screeningType(record.report?.report_type)}</Text></View><MaterialIcons name="chevron-right" size={20} color={c.muted} accessible={false}/></View>
    <View style={s.recordStates}><Status value={record.classification} prefix="Model"/><Status value={record.review?.status} prefix="Review"/></View>
    <Text style={[s.recordDate,{color:c.muted}]}>{dateLabel(record.date_generated)}</Text>
  </Pressable>
}

export function StudentRow({ student, onPress, onEdit }: { student: any; onPress: () => void; onEdit?:()=>void }) {
  const c = useColors()
  return <View style={[s.actionRow,{padding:0,borderBottomColor:c.border,borderBottomWidth:1,backgroundColor:c.surface}]}>
    <Pressable accessibilityRole="button" accessibilityLabel={'View history for '+student.full_name} onPress={onPress} android_ripple={{color:c.soft}}
      style={({pressed})=>[s.actionRow,{flex:1,minWidth:0,backgroundColor:pressed?c.soft:c.surface}]}>
      <Avatar name={student.full_name}/><View style={s.rowCopy}><Text accessibilityRole="header" style={[s.rowTitle,{color:c.text}]}>{student.full_name}</Text><Text style={[s.rowDetail,{color:c.muted}]}>Grade {student.grade_level}</Text></View>
      <MaterialIcons name="chevron-right" size={22} color={c.muted} accessible={false}/>
    </Pressable>
    {onEdit&&<Pressable accessibilityRole="button" accessibilityLabel={'Edit '+student.full_name} onPress={onEdit} style={{minHeight:48,minWidth:48,paddingRight:16,justifyContent:'center'}}><Text style={{color:c.primary,fontSize:14,fontWeight:'500'}}>Edit</Text></Pressable>}
  </View>
}

export function RecordValue({ label, value }: { label: string; value: string }) {
  const c=useColors()
  return <View style={{gap:5}}><Text style={{color:c.muted,fontSize:13,lineHeight:20}}>{label}</Text><Text style={{color:c.text,fontSize:15,lineHeight:23}}>{value}</Text></View>
}

export function ChoiceRow({ label, detail, selected, disabled, onPress }: { label:string;detail?:string;selected:boolean;disabled:boolean;onPress:()=>void }) {
  const c=useColors()
  return <Pressable accessibilityRole="radio" accessibilityLabel={label} accessibilityState={{checked:selected,disabled}} disabled={disabled} onPress={onPress}
    style={({pressed})=>[s.actionRow,{borderRadius:12,backgroundColor:selected||pressed?c.soft:c.surface,opacity:disabled ? .55 : 1}]}>
    <View style={s.rowCopy}><Text style={[s.rowTitle,{color:c.text}]}>{label}</Text>{detail&&<Text style={[s.rowDetail,{color:c.muted}]}>{detail}</Text>}</View>
    <MaterialIcons name={selected?'radio-button-checked':'radio-button-unchecked'} size={24} color={selected?c.primary:c.muted} accessible={false}/>
  </Pressable>
}

export const workspaceStyles = StyleSheet.create({
  group: { borderRadius:16, overflow:'hidden' },
  section: { gap:4 },
  headerButton: { minHeight:48,minWidth:48,alignItems:'center',justifyContent:'center',marginRight:8 },
})
const s = StyleSheet.create({
  brand:{flexDirection:'row',alignItems:'center',gap:8},wordmark:{fontSize:19,fontWeight:'700',letterSpacing:-.4},
  avatar:{alignItems:'center',justifyContent:'center'},
  sectionTitle:{flexDirection:'row',alignItems:'center',justifyContent:'space-between',gap:12,minHeight:48},sectionHeading:{flex:1,fontSize:18,lineHeight:25,fontWeight:'600'},
  textAction:{minHeight:48,justifyContent:'center',paddingLeft:12},
  actionRow:{flexDirection:'row',alignItems:'center',gap:14,padding:16,minHeight:80},rowCopy:{flex:1,minWidth:0,gap:4},
  rowTitle:{fontSize:16,lineHeight:23,fontWeight:'600'},rowDetail:{fontSize:13,lineHeight:20},
  screeningRow:{padding:16,gap:8},recordTop:{flexDirection:'row',alignItems:'center',gap:12},recordName:{flex:1,minWidth:0},recordStates:{flexDirection:'row',flexWrap:'wrap',gap:8},recordDate:{fontSize:12,lineHeight:18},
})
