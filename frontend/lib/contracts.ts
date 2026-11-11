import {z} from 'zod';

export const daily = z.object({
  simulation_date: z.iso.date({error:'Geçerli bir tarih seçin.'}),
  inverter_count: z.number().int().min(1).max(100),
  inverter_ac_rated_kw: z.number().positive(),
  inverter_dc_rated_kw: z.number().positive(),
  ekk_active_power_limit_kw: z.number().nonnegative(),
});
export type Profile = {username:string; full_name:string|null; email:string|null};
export type Summary = {
  id:number; simulation_date:string; created_at:string; inverter_count:number;
  processed_hours:number; total_inverter_energy_kwh:number; total_grid_energy_kwh:number;
  total_transformer_loss_kwh:number;
};
export type Hour = {
  hour:string; inverter_power_kw:number; grid_power_kw:number; irradiance_w_m2:number;
  ambient_temperature_c:number; transformer_loss_kw:number; ekk_limit_exceeded:boolean;
  available_active_power_kw?:number; curtailed_power_kw?:number; curtailed_energy_kwh?:number;
};
export type Detail = Summary & {
  inverter_ac_rated_kw:number; inverter_dc_rated_kw:number; ekk_active_power_limit_kw:number;
  total_curtailed_energy_kwh:number; transformer_efficiency:number; hourly_results:Hour[];
};
export type Comparison = {
  scenario_1:Pick<Detail,'id'>; scenario_2:Pick<Detail,'id'>;
  comparison:{grid_energy_difference_kwh:number; grid_energy_change_percent:number|null; same_weather_date:boolean};
};
export type Envelope<T> = {success:true; data:T};
export const number = (value:number) => new Intl.NumberFormat('tr-TR',{maximumFractionDigits:3}).format(value);
export const date = (value:string) => value.slice(0,10).split('-').reverse().join('.');
